# Copyright (C) 2013, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import logging
from pprint import pformat
import ast

from bdphpcprovider.cloudconnection import get_registered_vms, is_vm_running
from bdphpcprovider.platform import manage
from bdphpcprovider.corestages.stage import Stage
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler.errors import PackageFailedError
from bdphpcprovider.smartconnectorscheduler.stages.errors import InsufficientResourceError
from bdphpcprovider.sshconnection import open_connection
from bdphpcprovider.compute import run_command_with_status, run_make


from bdphpcprovider.runsettings import getval, setval, setvals, getvals, update, SettingNotFoundException

from bdphpcprovider.reliabilityframework.ftmanager import FTManager

from bdphpcprovider import messages
from bdphpcprovider import storage
from bdphpcprovider.corestages import stage
from bdphpcprovider.smartconnectorscheduler.stages.errors import \
    NoRegisteredVMError, VMTerminatedError

logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Bootstrap(Stage):
    """
    Schedules processes on a cloud infrastructure
    """

    def __init__(self, user_settings=None):
        logger.debug('Bootstrap stage initialised')

    def triggered(self, run_settings):

        try:
            created_str = getval(run_settings, '%s/stages/create/created_nodes' % RMIT_SCHEMA)
            self.created_nodes = ast.literal_eval(created_str)
            logger.debug('created_nodes=%s' % self.created_nodes)
            running_created_nodes = [x for x in self.created_nodes if str(x[3]) == 'running']
            logger.debug('running_created_nodes=%s' % running_created_nodes)
        except SettingNotFoundException:
            return False

        try:
            self.created_nodes = ast.literal_eval(created_str)
        except ValueError:
            return False
        if len(running_created_nodes) == 0:

            return False
        try:
            bootstrapped_str = getval(run_settings,
                                      '%s/stages/bootstrap/bootstrapped_nodes'
                                        % RMIT_SCHEMA)
            self.bootstrapped_nodes = ast.literal_eval(bootstrapped_str)
            logger.debug('bootstrapped nodes=%d, running created nodes = %d'
                         % (len(self.bootstrapped_nodes), len(running_created_nodes)))
            return len(self.bootstrapped_nodes) < len(running_created_nodes)
        except SettingNotFoundException:
            self.bootstrapped_nodes = []
            return True
        except ValueError:
            # FIXME: if failure parsing list, then assume not set for now.
            self.bootstrapped_nodes = []
            return True

        return False

    def process(self, run_settings):

        try:
            self.started = getval(run_settings,
                                  '%s/stages/bootstrap/started'
                                    % RMIT_SCHEMA)
        except SettingNotFoundException:
            self.started = 0
        # try:
        #     self.started = int(smartconnector.get_existing_key(run_settings,
        #         RMIT_SCHEMA + '/stages/bootstrap/started'))
        # except KeyError:
        #     self.started = 0

        logger.debug('self.started=%d' % self.started)
        messages.info(run_settings, "bootstrapping nodes")

        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        # local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]

        def retrieve_local_settings(run_settings, local_settings):

            update(local_settings, run_settings,
                '%s/stages/setup/payload_source' % RMIT_SCHEMA,
                '%s/stages/setup/payload_destination' % RMIT_SCHEMA,
                #'%s/system/platform',  # FIXME: Is this not used % RMIT_SCHEMA?
                '%s/stages/create/created_nodes' % RMIT_SCHEMA,
                '%s/stages/create/custom_prompt' % RMIT_SCHEMA
                   )
            # smartconnector.copy_settings(local_settings, run_settings,
            #     RMIT_SCHEMA + '/stages/setup/payload_source')
            # smartconnector.copy_settings(local_settings, run_settings,
            #     RMIT_SCHEMA + '/stages/setup/payload_destination')
            # smartconnector.copy_settings(local_settings, run_settings,
            #     RMIT_SCHEMA + '/system/platform')
            # smartconnector.copy_settings(local_settings, run_settings,
            #     RMIT_SCHEMA + '/stages/create/created_nodes')
            # smartconnector.copy_settings(local_settings, run_settings,
            #     RMIT_SCHEMA + '/stages/create/custom_prompt')

            local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)
            # local_settings['bdp_username'] = run_settings[
            #     RMIT_SCHEMA + '/bdp_userprofile']['username']

            computation_platform_url = getval(run_settings, '%s/platform/computation/platform_url' % RMIT_SCHEMA)
            # computation_platform_url = run_settings['http://rmit.edu.au/schemas/platform/computation']['platform_url']
            comp_pltf_settings = manage.get_platform_settings(computation_platform_url, local_settings['bdp_username'])
            local_settings.update(comp_pltf_settings)
            # computation_platform_url = run_settings['http://rmit.edu.au/schemas/platform/computation']['platform_url']
            # logger.debug("computation_platform_url=%s" % computation_platform_url)
            # comp_pltf_settings = manage.get_platform_settings(computation_platform_url, local_settings['bdp_username'])
            # local_settings.update(comp_pltf_settings)

            logger.debug("local_settings=%s" % local_settings)
            logger.debug('retrieve completed')

        retrieve_local_settings(run_settings, local_settings)
        logger.debug("local_settings=%s" % pformat(local_settings))
        if not self.started:
            try:
                logger.debug('process to start')
                start_multi_setup_task(local_settings)
            except PackageFailedError, e:
                logger.error("unable to start setup of packages: %s" % e)
            except Exception, e:
                logger.debug(e)
                raise
            pass
            self.started = 1

        else:
            try:
                self.nodes = get_registered_vms(local_settings)
                running_created_nodes = [x for x in self.created_nodes if str(x[3]) == 'running']
                if len(self.nodes) < len(running_created_nodes):
                    raise VMTerminatedError
            except NoRegisteredVMError as e:
                logger.debug('NoRegisteredVMError detected')
                ftmanager = FTManager()
                ftmanager.manage_failure(e, stage_class=self,  settings=local_settings)
            except VMTerminatedError as e:
                logger.debug('VMTerminatedError detected')
                ftmanager = FTManager()
                ftmanager.manage_failure(e, stage_class=self,  settings=local_settings)
            self.error_nodes = []
            for node in self.nodes:
                node_ip = node.ip_address
                if not node_ip:
                    node_ip = node.private_ip_address
                if (node_ip in [x[1]
                                        for x in self.bootstrapped_nodes
                                        if x[1] == node_ip]):
                    continue
                relative_path = "%s@%s" % (local_settings['type'],
                    local_settings['payload_destination'])
                destination = stage.get_url_with_pkey(local_settings,
                    relative_path,
                    is_relative_path=True,
                    ip_address=node_ip)
                logger.debug("Relative path %s" % relative_path)
                logger.debug("Destination %s" % destination)
                try:
                    fin = job_finished(node_ip, local_settings, destination)
                except IOError, e:
                    logger.error(e)
                    fin = False
                except Exception as e:
                    logger.error(e)
                    fin = False
                    ftmanager = FTManager()
                    ftmanager.manage_failure(e, stage_class=self, vm_ip=node_ip,
                                             vm_id=node.id, settings=local_settings)
                logger.debug("fin=%s" % fin)
                if fin:
                    print "done."
                    logger.debug("node=%s" % str(node))
                    logger.debug("bootstrapped_nodes=%s" % self.bootstrapped_nodes)
                    if not (node_ip in [x[1]
                                                for x in self.bootstrapped_nodes
                                                if x[1] == node_ip]):
                        logger.debug('new ip = %s' % node_ip)
                        self.bootstrapped_nodes.append(
                            [node.id, node_ip, unicode(node.region), 'running'])
                    else:
                        logger.info("We have already "
                            + "bootstrapped node %s" % node_ip)
                    messages.info(run_settings, "bootstrapping nodes (%s nodes done)"
                        % len(self.bootstrapped_nodes))
                else:
                    print "job still running on %s" % node_ip

    def output(self, run_settings):
        setvals(run_settings, {
                '%s/stages/bootstrap/started' % RMIT_SCHEMA: self.started,
                '%s/stages/bootstrap/bootstrapped_nodes' % RMIT_SCHEMA: str(self.bootstrapped_nodes),
                '%s/system/id' % RMIT_SCHEMA: 0,
                '%s/stages/create/created_nodes' % RMIT_SCHEMA: self.created_nodes
                })
        running_created_nodes = [x for x in self.created_nodes if x[3] == 'running']
        logger.debug('running created_nodes=%s' % running_created_nodes)
        if self.bootstrapped_nodes and len(self.bootstrapped_nodes) == len(running_created_nodes):
            setvals(run_settings, {
                '%s/stages/bootstrap/bootstrap_done' % RMIT_SCHEMA: 1})
        return run_settings


def start_multi_setup_task(settings):
    """
    Run the package on each of the nodes in the group and grab
    any output as needed
    """
    nodes = get_registered_vms(settings)
    logger.debug("nodes=%s" % nodes)
    requested_nodes = 0
    maketarget_nodegroup_pair = {}

    # TODO: need testcases for following code
    if not maketarget_nodegroup_pair:
        EMPTY_MAKE_TARGET = ''
        requested_nodes = len(nodes)
        maketarget_nodegroup_pair[EMPTY_MAKE_TARGET] = requested_nodes
    else:
        for i in maketarget_nodegroup_pair.keys():
            requested_nodes += maketarget_nodegroup_pair[i]
        if requested_nodes > len(nodes):
            message = "Requested nodes %d; but available nodes %s " \
                % (requested_nodes, len(nodes))
            logger.exception(message)
            raise InsufficientResourceError(message)
    logger.info("Requested nodes %d: \nAvailable nodes %s "
           % (requested_nodes, len(nodes)))

    logger.debug('starting setup')
    for make_target in maketarget_nodegroup_pair:
        for i in range(0, maketarget_nodegroup_pair[make_target]):
            instance = nodes[0]
            node_ip = instance.ip_address
            if not node_ip:
                node_ip = instance.private_ip_address
            logger.debug("node_ip=%s" % node_ip)
            logger.debug('constructing source')
            source = stage.get_url_with_pkey(settings, settings['payload_source'])
            logger.debug('source=%s' % source)
            relative_path = '%s@%s' % (settings['type'], settings['payload_destination'])
            destination = stage.get_url_with_pkey(settings, relative_path,
                                                 is_relative_path=True,
                                                 ip_address=node_ip)
            logger.debug("Source %s" % source)
            logger.debug("Destination %s" % destination)
            logger.debug("Relative path %s" % relative_path)
            start_setup(instance, node_ip, settings, source, destination)
            nodes.pop(0)


def start_setup(instance, ip,  settings, source, destination):
    """
        Start the task on the instance, then return
    """
    logger.info("run_task %s" % str(instance))
    storage.copy_directories(source, destination)
    makefile_path = storage.get_make_path(destination)
    # TODO, FIXME:  need to have timeout for yum install make
    # and then test can access, otherwise, loop.
    install_make = 'yum install -y make'
    command_out = ''
    errs = ''
    logger.debug("starting command for %s" % ip)
    ssh = ''
    try:
        ssh = open_connection(ip_address=ip, settings=settings)
        command_out, errs = run_command_with_status(ssh, install_make)
        logger.debug("command_out1=(%s, %s)" % (command_out, errs))
        run_make(ssh, makefile_path, 'setupstart')
    except Exception, e:#fixme: consider using reliability framework
        logger.error(e)
        raise
    finally:
        if ssh:
            ssh.close()


def job_finished(ip, settings, destination):
    """
        Return True if package job on instance_id has job_finished
    """
    ssh = open_connection(ip_address=ip, settings=settings)
    makefile_path = storage.get_make_path(destination)
    (command_out, err) = run_make(ssh, makefile_path, 'setupdone')
    if command_out:
        logger.debug("command_out = %s" % command_out)
        for line in command_out:
            if 'Environment Setup Completed' in line:
                return True
    else:
        logger.warn(err)
    return False
