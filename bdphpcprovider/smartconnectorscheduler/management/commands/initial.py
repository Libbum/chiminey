
import os
import logging
import logging.config

from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand

from bdphpcprovider.smartconnectorscheduler import models


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Load up the initial state of the database (replaces use of
    fixtures).  Assumes specific strcture.
    NB: passwords are wrong and will need to be changed in the admin
    tool.
    """

    args = ''
    help = 'Setup an initial task structure.'

    def setup(self):
        confirm = raw_input("This will ERASE and reset the database.  Are you sure [Yes|No]")
        if confirm != "Yes":
            print "action aborted by user"
            return


        self.group, _ = Group.objects.get_or_create(name="standarduser")
        self.group.save()

        for model_name in ('userprofileparameter', 'userprofileparameterset'):
            #add_model = Permission.objects.get(codename="add_%s" % model_name)
            change_model = Permission.objects.get(codename="change_%s" % model_name)
            #delete_model = Permission.objects.get(codename="delete_%s" % model_name)
            #self.group.permissions.add(add_model)
            self.group.permissions.add(change_model)
            #self.group.permissions.add(delete_model)

        self.group.save()

        # # Create a user and profile
        # self.user, _ = User.objects.get_or_create(username="username1",
        #     defaults={"password": "password"})
        # self.user.groups.add(self.group)
        # self.user.save()

        # logger.debug("user=%s" % self.user)
        # profile, _ = models.UserProfile.objects.get_or_create(
        #               user=self.user)

        # Create the schemas for template parameters or config info
        # specfied in directive arguments
        # for ns, name, desc in [(models.UserProfile.PROFILE_SCHEMA_NS,
        #     "userprofile1", "Information about user"),
        #     ('http://rmit.edu.au/schemas/greeting/salutation', "salutation",
        #         "The form of salutation"),
        #     ("http://rmit.edu.au/schemas/program", "program",
        #         "A remote executing program"),
        #      ('http://tardis.edu.au/schemas/hrmc/dfmeta/', "datafile1",
        #         "datafile 1 schema"),
        #     ('http://tardis.edu.au/schemas/hrmc/dfmeta2/', "datafile2",
        #         "datafile 2 schema"),
        #     ('http://tardis.edu.au/schemas/hrmc/create', "create",
        #         "create stage"),
        #     ("http://nci.org.au/schemas/hrmc/custom_command/", "custom",
        #         "custom command")
        #     ]:
        #     sch, _ = models.Schema.objects.get_or_create(namespace=ns, name=name, description=desc)
        #     logger.debug("sch=%s" % sch)



        # user_schema = models.Schema.objects.get(namespace=models.UserProfile.PROFILE_SCHEMA_NS)
        # # Create the schema for stages (currently only one) and all allowed
        # # values and their types for all stages.
        # context_schema, _ = models.Schema.objects.get_or_create(
        #     namespace=models.Context.CONTEXT_SCHEMA_NS,
        #     name="Context Schema", description="Schema for run settings")
        # # We assume that a run_context has only one schema at the moment, as
        # # we have to load up this schema with all run settings values used in
        # # any of the stages (and any parameters required for the stage
        # # invocation)
        # # TODO: allow multiple ContextParameterSet each with different schema
        # # so each value will come from a namespace.  e.g., general/fsys
        # # nectar/num_of_nodes, setup/nodes_setup etc.
        # for name, param_type in {
        #     u'file0': models.ParameterName.STRING,
        #     u'file1': models.ParameterName.STRING,
        #     u'file2': models.ParameterName.STRING,
        #     u'program': models.ParameterName.STRING,
        #     u'remotehost': models.ParameterName.STRING,
        #     u'salutation': models.ParameterName.NUMERIC,
        #     u'transitions': models.ParameterName.STRING,  # TODO: use STRLIST
        #     u'program_output': models.ParameterName.NUMERIC,
        #     u'movement_output': models.ParameterName.NUMERIC,
        #     u'platform': models.ParameterName.NUMERIC,
        #     u'system': models.ParameterName.STRING,
        #     u'num_nodes': models.ParameterName.NUMERIC,
        #     u'program_success': models.ParameterName.STRING,
        #     u'iseed': models.ParameterName.NUMERIC,
        #     u'command': models.ParameterName.STRING,
        #     u'null_output': models.ParameterName.NUMERIC,
        #     u'parallel_output': models.ParameterName.NUMERIC,
        #     u'null_number': models.ParameterName.NUMERIC,
        #     u'parallel_number': models.ParameterName.NUMERIC,
        #     u'null_index': models.ParameterName.NUMERIC,
        #     u'parallel_index': models.ParameterName.NUMERIC,
        #     }.items():
        #     models.ParameterName.objects.get_or_create(schema=context_schema,
        #         name=name,
        #         type=param_type)

        # self.PARAMTYPE = {'userinfo1': models.ParameterName.STRING,
        #     'userinfo2': models.ParameterName.NUMERIC,
        #     'fsys': models.ParameterName.STRING,
        #     'nci_user': models.ParameterName.STRING,
        #     'nci_password': models.ParameterName.STRING,
        #     'nci_host': models.ParameterName.STRING,
        #     'PASSWORD': models.ParameterName.STRING,
        #     'USER_NAME': models.ParameterName.STRING,
        #     'PRIVATE_KEY': models.ParameterName.STRING}
        # for k, v in self.PARAMTYPE.items():
        #     param_name, _ = models.ParameterName.objects.get_or_create(schema=user_schema,
        #         name=k,
        #         type=self.PARAMTYPE[k])

        schema_data = {
            u'http://rmit.edu.au/schemas//files':
                [u'general input files for directive',
                {
                u'file0': models.ParameterName.STRING,
                u'file1': models.ParameterName.STRING,
                u'file2': models.ParameterName.STRING,
                }
                ],
             # Note that file schema ns must match regex
             # protocol://host/schemas/{directective.name}/files
             # otherwise files will not be matched correctly.
             # TODO: make fall back to directive files in case specfici
             # version not defined here.
             u'http://rmit.edu.au/schemas/smartconnector1/files':
                 [u'the smartconnector1 input files',
                 {
                 u'file0': models.ParameterName.STRING,
                 u'file1': models.ParameterName.STRING,
                 u'file2': models.ParameterName.STRING,
                 }
                 ],
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                [u'the smartconnector1 create stage config',
                {
                u'iseed': models.ParameterName.NUMERIC,
                u'num_nodes': models.ParameterName.NUMERIC,
                u'null_number': models.ParameterName.NUMERIC,
                u'parallel_number': models.ParameterName.NUMERIC,
                }
                ],
            # we might want to reuse schemas in muliple contextsets
            # hence we could merge next too stages, for example.
            # However, current ContextParameterSets are unamed in the
            # URI so we can't identify which one to use.
            u'http://rmit.edu.au/schemas/stages/null/testing':
                [u'the null stage internal testing',
                {
                u'output': models.ParameterName.NUMERIC,
                u'index': models.ParameterName.NUMERIC,
                }
                ],
            u'http://rmit.edu.au/schemas/stages/parallel/testing':
                [u'the parallel stage internal testing',
                {

                u'output': models.ParameterName.NUMERIC,
                u'index': models.ParameterName.NUMERIC
                }
                ],
            u'http://nci.org.au/schemas/smartconnector1/custom':
                [u'the smartconnector1 custom command',
                {
                u'command': models.ParameterName.STRING
                }
                ],
            u'http://rmit.edu.au/schemas/system/misc':
                [u'system level misc values',
                {
                u'transitions': models.ParameterName.STRING,  # deprecated
                u'system': models.ParameterName.STRING,
                u'id': models.ParameterName.NUMERIC
                }
                ],
            u'http://rmit.edu.au/schemas/system':
                [u'Information about the deployment platform',
                {
                u'platform': models.ParameterName.STRING,  # deprecated
                }
                ],
            u'http://tardis.edu.au/schemas/hrmc/dfmeta':
                ["datafile",
                {
                u"a": models.ParameterName.NUMERIC,
                u'b': models.ParameterName.NUMERIC,
                }
                ],
            u'http://tardis.edu.au/schemas/hrmc/dfmeta2':
                ["datafile2",
                {
                u'c': models.ParameterName.STRING,
                }
                ],
            models.UserProfile.PROFILE_SCHEMA_NS:
                [u'user profile',
                {
                    u'userinfo1': models.ParameterName.STRING,
                    u'userinfo2': models.ParameterName.NUMERIC,
                    u'fsys': models.ParameterName.STRING,
                    u'nci_user': models.ParameterName.STRING,
                    u'nci_password': models.ParameterName.STRING,
                    u'nci_host': models.ParameterName.STRING,
                    u'PASSWORD': models.ParameterName.STRING,
                    u'USER_NAME': models.ParameterName.STRING,
                    u'PRIVATE_KEY': models.ParameterName.STRING,
                    u'flag': models.ParameterName.NUMERIC,
                    u'CLOUD_SLEEP_INTERVAL': models.ParameterName.NUMERIC,
                    u'local_fs_path': models.ParameterName.STRING,
                    u'PRIVATE_KEY_NAME': models.ParameterName.STRING,
                    u'PRIVATE_KEY_NECTAR': models.ParameterName.STRING,
                    u'PRIVATE_KEY_NCI': models.ParameterName.STRING,
                    u'EC2_ACCESS_KEY': models.ParameterName.STRING,
                    u'EC2_SECRET_KEY': models.ParameterName.STRING
                }
                ],
            u'http://rmit.edu.au/schemas/copy/files':
                 [u'the copy input files',
                 {
                 u'file0': models.ParameterName.STRING,
                 u'file1': models.ParameterName.STRING,
                 }
                 ],
            u'http://rmit.edu.au/schemas/program/files':
                 [u'the copy input files',
                 {
                 u'file0': models.ParameterName.STRING,
                 u'file1': models.ParameterName.STRING,
                 u'file2': models.ParameterName.STRING,
                 }
                 ],
            u'http://rmit.edu.au/schemas/stages/copy/testing':
                [u'the copy stage internal testing',
                {
                u'output': models.ParameterName.NUMERIC,
                }
                ],
            u'http://rmit.edu.au/schemas/stages/program/testing':
                [u'the program stage internal testing',
                {
                u'output': models.ParameterName.NUMERIC,
                }
                ],
            u'http://rmit.edu.au/schemas/program/config':
                [u'the program command internal config',
                {
                u'program': models.ParameterName.STRING,
                u'remotehost': models.ParameterName.STRING,
                u'program_success': models.ParameterName.STRING
                }
                ],
            u'http://rmit.edu.au/schemas/greeting/salutation':
                [u'salute',
                {
                    u'salutation': models.ParameterName.STRING
                }
                ],
            u'http://rmit.edu.au/schemas/hrmc':
                [u'the hrmc smart connector input values',
                {
                    u'number_vm_instances': models.ParameterName.NUMERIC,
                    u'iseed': models.ParameterName.NUMERIC
                }
                ],
            u'http://rmit.edu.au/schemas/stages/create':
                [u'the create state of the smartconnector1',
                {
                u'group_id': models.ParameterName.STRING,
                u'VM_SIZE': models.ParameterName.STRING,
                u'VM_IMAGE': models.ParameterName.STRING,
                u'CLOUD_SLEEP_INTERVAL': models.ParameterName.NUMERIC,
                }
                ],

            u'http://rmit.edu.au/schemas/stages/setup':
                [u'the create stage of the smartconnector1',
                {
                u'setup_finished': models.ParameterName.NUMERIC,
                u'PAYLOAD_SOURCE': models.ParameterName.STRING,
                u'PAYLOAD_DESTINATION': models.ParameterName.STRING,
                u'SECURITY_GROUP': models.ParameterName.STRLIST,
                u'GROUP_ID_DIR': models.ParameterName.STRING,
                u'CUSTOM_PROMPT': models.ParameterName.STRING,
                }
                ],
        }


        from urlparse import urlparse
        from django.template.defaultfilters import slugify

        for ns in schema_data:
            l = schema_data[ns]
            logger.debug("l=%s" % l)
            desc = l[0]
            logger.debug("desc=%s" % desc)
            kv = l[1:][0]
            logger.debug("kv=%s", kv)

            url = urlparse(ns)

            context_schema, _ = models.Schema.objects.get_or_create(
                namespace=ns, defaults={'name': slugify(url.path), 'description': desc})

            for k, v in kv.items():
                models.ParameterName.objects.get_or_create(schema=context_schema,
                    name=k, defaults={'type': v})

        # for name, param_type in {
        #     u'file0': models.ParameterName.STRING,
        #     u'file1': models.ParameterName.STRING,
        #     u'file2': models.ParameterName.STRING,
        #     u'program': models.ParameterName.STRING,
        #     u'remotehost': models.ParameterName.STRING,
        #     u'salutation': models.ParameterName.NUMERIC,
        #     u'transitions': models.ParameterName.STRING,  # TODO: use STRLIST
        #     u'program_output': models.ParameterName.NUMERIC,
        #     u'movement_output': models.ParameterName.NUMERIC,
        #     u'platform': models.ParameterName.STRING,
        #     u'system': models.ParameterName.STRING,
        #     u'num_nodes': models.ParameterName.NUMERIC,
        #     u'iseed': models.ParameterName.NUMERIC,
        #     u'number_vm_instances': models.ParameterName.NUMERIC,
        #     u'command': models.ParameterName.STRING,
        #     u'null_output': models.ParameterName.NUMERIC,
        #     u'parallel_output': models.ParameterName.NUMERIC,
        #     u'USER_NAME': models.ParameterName.STRING,
        #     u'PASSWORD':models.ParameterName.STRING,
        #     u'SECURITY_GROUP': models.ParameterName.STRLIST,
        #     u'VM_SIZE': models.ParameterName.STRING,
        #     u'VM_IMAGE': models.ParameterName.STRING,
        #     u'GROUP_ID_DIR': models.ParameterName.STRING,
        #     u'CUSTOM_PROMPT': models.ParameterName.STRING,
        #     u'group_id': models.ParameterName.STRING,
        #     u'flag': models.ParameterName.NUMERIC,
        #     u'CLOUD_SLEEP_INTERVAL': models.ParameterName.NUMERIC,
        #     u'setup_finished': models.ParameterName.NUMERIC,
        #     u'id': models.ParameterName.NUMERIC,
        #     u'PAYLOAD_SOURCE': models.ParameterName.STRING,
        #     u'PAYLOAD_DESTINATION': models.ParameterName.STRING,
        #     u'local_fs_path': models.ParameterName.STRING
        #     }.items():


        # # Make a platform for the commands
        # platform, _ = models.Platform.objects.get_or_create(name="nectar")

        copy_dir, _ = models.Directive.objects.get_or_create(name="copy")
        program_dir, _ = models.Directive.objects.get_or_create(name="program")
        smart_dir, _ = models.Directive.objects.get_or_create(name="smartconnector1")

        hrmc_smart_dir, _ = models.Directive.objects.get_or_create(name="smartconnector_hrmc")

        self.movement_stage = "bdphpcprovider.smartconnectorscheduler.stages.movement.MovementStage"
        self.program_stage = "bdphpcprovider.smartconnectorscheduler.stages.program.ProgramStage"
        # Define all the stages that will make up the command.  This structure
        # has two layers of composition
        copy_stage, _ = models.Stage.objects.get_or_create(name="copy",
             description="data movemement operation",
             package=self.movement_stage,
             order=100)
        copy_stage.update_settings({})

        program_stage, _ = models.Stage.objects.get_or_create(name="program",
            description="program execution stage",
            package=self.program_stage,
            order=0)
        program_stage.update_settings({})

        self.null_package = "bdphpcprovider.smartconnectorscheduler.stages.nullstage.NullStage"
        self.parallel_package = "bdphpcprovider.smartconnectorscheduler.stages.composite.ParallelStage"
        # Define all the stages that will make up the command.  This structure
        # has two layers of composition
        composite_stage, _ = models.Stage.objects.get_or_create(name="basic_connector",
             description="encapsulates a workflow",
             package=self.parallel_package,
             order=100)

        setup_stage,_ = models.Stage.objects.get_or_create(name="setup",
            parent=composite_stage,
            description="This is a setup stage of something",
            package=self.null_package,
            order=0)

        # stage settings are usable from subsequent stages in a run so only
        # need to define once for first null or parallel stage
        setup_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                {
                    u'null_number': 4,
                }
            })

        stage2, _ = models.Stage.objects.get_or_create(name="run",
            parent=composite_stage,
            description="This is the running connector",
            package=self.parallel_package,
            order=1)

        stage2.update_settings(
            {
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                {
                    u'parallel_number': 2
                }
            })

        models.Stage.objects.get_or_create(name="run1",
            parent=stage2,
            description="This is the running part 1",
            package=self.null_package,
            order=1)

        models.Stage.objects.get_or_create(name="run2",
            parent=stage2,
            description="This is the running part 2",
            package=self.null_package,
            order=2)

        models.Stage.objects.get_or_create(name="finished",
            parent=composite_stage,
            description="And here we finish everything off",
            package=self.null_package,
            order=3)

        self.configure_package = "bdphpcprovider.smartconnectorscheduler.stages.configure.Configure"
        self.create_package = "bdphpcprovider.smartconnectorscheduler.stages.create.Create"
        self.setup_package = "bdphpcprovider.smartconnectorscheduler.stages.setup.Setup"

        hrmc_composite_stage, _ = models.Stage.objects.get_or_create(name="hrmc_connector",
                                                                description="Encapsultes HRMC smart connector workflow",
                                                                package=self.parallel_package,
                                                                order=100)

        # FIXME: tasks.progress_context does not load up composite stage settings
        hrmc_composite_stage.update_settings({})

        configure_stage, _ = models.Stage.objects.get_or_create(name="configure",
                                                                description="This is configure stage of HRMC smart connector",
                                                                parent=hrmc_composite_stage,
                                                                package=self.configure_package,
                                                                order=0)
        configure_stage.update_settings({})

        create_stage, _ = models.Stage.objects.get_or_create(name="create",
                                                                description="This is create stage of HRMC smart connector",
                                                                #parent=hrmc_composite_stage,
                                                                package=self.create_package,
                                                                order=1)

        create_stage.update_settings({})

        setup_stage, _ = models.Stage.objects.get_or_create(name="setup",
                                                             description="This is setup stage of HRMC smart connector",
                                                             parent=hrmc_composite_stage,
                                                             package=self.setup_package,
                                                             order=1)

        setup_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/setup':
                {
                    u'PAYLOAD_SOURCE': 'file://127.0.0.1/local/testpayload',
                    u'PAYLOAD_DESTINATION': 'nectar@celery_payload_2',
                    u'SECURITY_GROUP': '["ssh"]',
                    u'GROUP_ID_DIR': 'group_id',
                    u'CUSTOM_PROMPT': '[smart-connector_prompt]$'
                },
            u'http://rmit.edu.au/schemas/stages/create':
                {
                    u'VM_SIZE': "m1.small",
                    u'VM_IMAGE': "ami-0000000d",
                    u'CLOUD_SLEEP_INTERVAL': 5
                },
            })

        # Need to create Parmetersets for stages here and associate with these stages

        logger.debug("stages=%s" % models.Stage.objects.all())
        local_filesys_rootpath = '/opt/cloudenabling/current/bdphpcprovider/smartconnectorscheduler/testing/remotesys'
        models.Platform.objects.get_or_create(name='local', root_path=local_filesys_rootpath)
        models.Platform.objects.get_or_create(name='nectar', root_path='/home/centos')
        platform, _  = models.Platform.objects.get_or_create(name='nci', root_path=local_filesys_rootpath)




        # Make a new command that reliases composite_stage
        # TODO: add the command program to the model
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=copy_dir, stage=copy_stage)
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=program_dir, stage=program_stage)
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=smart_dir, stage=composite_stage)
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=hrmc_smart_dir, stage=hrmc_composite_stage)


        # We could make one command with a composite containing three stages or
        # three commands each containing a single stage.

        # done setup

        logger.debug("local_filesys_rootpath=%s" % local_filesys_rootpath)

        # self.remote_fs_path = os.path.join(
        #     'smartconnectorscheduler', 'testing', 'remotesys/').decode("utf8")
        # logger.debug("self.remote_fs_path=%s" % self.remote_fs_path)
        local_fs = FileSystemStorage(location=local_filesys_rootpath)

        local_fs.save("local/greet.txt",
            ContentFile("{{salutation}} World"))

        local_fs.save("remote/greetaddon.txt",
            ContentFile("(remotely)"))

        # setup the required initial files
        local_fs.save("input/input.txt",
         ContentFile("a={{a}} b={{b}} c={{c}}"))

        local_fs.save("input/file.txt",
         ContentFile("foobar"))
        print "done"

    def handle(self, *args, **options):
        self.setup()
        print "done"
