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

import os
import logging

from django.contrib.auth.models import User
from bdphpcprovider.smartconnectorscheduler import models
from django.db.models import ObjectDoesNotExist

logger = logging.getLogger(__name__)


def create_platform_paramset(username, schema_namespace,
                             parameters, filter_field=None):
    params_present, provided_params, required_params = \
        all_params_present(schema_namespace, parameters)
    if not params_present:
        logger.debug('Cannot create platform. \n Required params= %s'
                     ' \n Provided params= %s ' % (required_params, provided_params))
        return False
    owner = get_owner(username)
    if not owner:
        logger.debug('username=%s unknown' % username)
        return False
    if not filter_field:
        filter_field = parameters
    platform, _ = models.PlatformInstance.objects.get_or_create(
       owner=owner, schema_namespace_prefix=schema_namespace)
    schema, _ = models.Schema.objects.get_or_create(namespace=schema_namespace)
    unique = is_unique_platform_paramset(
        username, schema_namespace, filter_field)
    logger.debug('unique parameter set %s' % unique)
    if unique:
         param_set = models.PlatformInstanceParameterSet.objects\
             .create(platform=platform, schema=schema)
         for k, v in parameters.items():
            try:
                param_name = models.ParameterName.objects\
                    .get(schema=schema, name=k)
            except ObjectDoesNotExist as e:
                logger.debug('Skipping unrecognized parameter name: %s' % k)
                continue
            models.PlatformInstanceParameter.objects\
                .get_or_create(name=param_name, paramset=param_set, value=v)
         return True
    return False


def retrieve_platform_paramsets(username, schema_namespace):
    recorded_platforms = []
    owner = get_owner(username)
    if not owner:
        logger.debug('username=%s unknown' % username)
        return recorded_platforms
    platforms = models.PlatformInstance.objects.filter(
       owner=owner, schema_namespace_prefix__startswith=schema_namespace)
    for platform in platforms:
        platform_type = os.path.basename(platform.schema_namespace_prefix)
        param_sets = models.PlatformInstanceParameterSet\
            .objects.filter(platform=platform)
        for param_set in param_sets:
            platform_parameters = models.PlatformInstanceParameter\
                .objects.filter(paramset=param_set)
            platform_record = {}
            for platform_parameter in platform_parameters:
                platform_record[platform_parameter.name.name] = platform_parameter.value
            platform_record['type'] = platform_type
            recorded_platforms.append(platform_record)
    return recorded_platforms


def delete_platform_paramsets(username, schema_namespace, filter_field):
    if not filter_field:
        logger.debug('Filter field should not be empty. Exiting...')
        return
    platform, schema = get_platform_and_schema(username, schema_namespace)
    if (not platform) or (not schema):
        logger.debug('unknown username [%s] and/or schema namespace [%s]. Exiting...'
                     % (username, schema_namespace))
        return
    param_sets = filter_platform_paramsets(platform, schema, filter_field)
    for param_set in param_sets:
        logger.debug('deleting ... %s' % param_set)
        param_set.delete()


def update_platform_paramsets(username, schema_namespace,
                              old_parameters, new_parameters):
    if create_platform_paramset(username, schema_namespace, new_parameters):
        delete_platform_paramsets(username, schema_namespace, old_parameters)


def is_unique_platform_paramset(platform, schema, filter_field):
    if not filter_field:
        logger.debug('Filter field should not be empty. Exiting...')
        return False
    param_sets = filter_platform_paramsets(
        platform, schema, filter_field)
    if param_sets:
        return False
    return True


def filter_platform_paramsets(platform, schema, filter_field):
    #unknown_filter_field = False
    param_sets = models.PlatformInstanceParameterSet\
        .objects.filter(platform=platform)
    for k, v in filter_field.items():
        logger.debug('k=%s, v=%s' % (k, v))
        try:
            param_name = models.ParameterName.objects.get(
                schema=schema, name=k)
        except ObjectDoesNotExist as e:
            logger.debug('Skipping unrecognized parametername: %s' % k)
            #unknown_filter_field = True
            continue
        except Exception:
            raise
        potential_paramsets = []
        for param_set in param_sets:
            logger.debug('Analysing %s' % param_set.pk)
            try:
                models.PlatformInstanceParameter.objects.get(
                    name=param_name, paramset=param_set, value=v)
                potential_paramsets.append(param_set)
            except ObjectDoesNotExist as e:
                logger.debug('%s is removed' % param_set.pk)
            except Exception:
                raise
        param_sets = list(potential_paramsets)
    return param_sets#, unknown_filter_field


def get_owner(username):
    owner = None
    try:
        user = User.objects.get(username=username)
        owner = models.UserProfile.objects.get(user=user)
    except ObjectDoesNotExist as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)
        raise
    return owner


def get_platform_and_schema(username, schema_namespace):
    platform = None
    schema = None
    owner = get_owner(username)
    if owner:
        try:
            platform = models.PlatformInstance.objects.get(
                owner=owner, schema_namespace_prefix=schema_namespace)
            schema = models.Schema.objects.get(namespace=schema_namespace)
        except ObjectDoesNotExist as e:
            logger.exception(e)
        except Exception as e:
            logger.exception(e)
            raise
    return (platform, schema)


def all_params_present(schema_namespace, parameters):
    schema = models.Schema.objects.get(namespace=schema_namespace)
    required_params= models.ParameterName.objects.filter(schema=schema)
    required_params_names = [x.name for x in required_params]
    provided_params_names = [x for x in required_params_names if x in parameters]
    if len(provided_params_names) == len(required_params_names):
        return True, provided_params_names, required_params_names
    return False, provided_params_names, required_params_names