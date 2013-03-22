"""
Management utility to create users.
"""

import getpass
import re
import sys

from optparse import make_option
from django.contrib.auth.models import User, Group
from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

from bdphpcprovider.smartconnectorscheduler import models


RE_VALID_USERNAME = re.compile('[\w.@+-]+$')

EMAIL_RE = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"'  # quoted-string
    r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$', re.IGNORECASE)  # domain


def is_valid_email(value):
    if not EMAIL_RE.search(value):
        raise exceptions.ValidationError(_('Enter a valid e-mail address.'))


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default=None,
            help='Specifies the username for the user.'),
        make_option('--email', dest='email', default=None,
            help='Specifies the email address for the user.'),
        make_option('--remotefsys', dest='remotefsys', default="/opt/cloudenabling/current/bdphpcprovider/smartconnectorscheduler/testing/remotesys/",
            help='Specifies the email address for the user.'),
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help=('Tells Django to NOT prompt the user for input of any kind. '
                  'You must use --username and --email with --noinput.')),
    )

    help = 'Used to create a BDPHPCProvider user.'

    def handle(self, *args, **options):
        username = options.get('username', None)
        email = options.get('email', None)
        interactive = options.get('interactive')
        remotefsys = options.get('remotefsys')
        verbosity = int(options.get('verbosity', 1))

        # Do quick and dirty validation if --noinput
        if not interactive:
            if not username or not email:
                raise CommandError("You must use --username and --email with --noinput.")
            if not RE_VALID_USERNAME.match(username):
                raise CommandError("Invalid username. Use only letters, digits, and underscores")
            try:
                is_valid_email(email)
            except exceptions.ValidationError:
                raise CommandError("Invalid email address.")

        # If not provided, create the user with an unusable password
        password = None

        # Try to determine the current system user's username to use as a default.
        try:
            default_username = getpass.getuser().replace(' ', '').lower()
        except (ImportError, KeyError):
            # KeyError will be raised by os.getpwuid() (called by getuser())
            # if there is no corresponding entry in the /etc/passwd file
            # (a very restricted chroot environment, for example).
            default_username = ''

        # Determine whether the default username is taken, so we don't display
        # it as an option.
        if default_username:
            try:
                User.objects.get(username=default_username)
            except User.DoesNotExist:
                pass
            else:
                default_username = ''

        # Prompt for username/email/password. Enclose this whole thing in a
        # try/except to trap for a keyboard interrupt and exit gracefully.
        if interactive:
            try:

                # Get a username
                while 1:
                    if not username:
                        input_msg = 'Username'
                        if default_username:
                            input_msg += ' (Leave blank to use %r)' % default_username
                        username = raw_input(input_msg + ': ')
                    if default_username and username == '':
                        username = default_username
                    if not RE_VALID_USERNAME.match(username):
                        sys.stderr.write("Error: That username is invalid. Use only letters, digits and underscores.\n")
                        username = None
                        continue
                    try:
                        User.objects.get(username=username)
                    except User.DoesNotExist:
                        break
                    else:
                        sys.stderr.write("Error: That username is already taken.\n")
                        username = None

                # Get an email
                while 1:
                    if not email:
                        email = raw_input('E-mail address: ')
                    try:
                        is_valid_email(email)
                    except exceptions.ValidationError:
                        sys.stderr.write("Error: That e-mail address is invalid.\n")
                        email = None
                    else:
                        break

                # Get a password
                while 1:
                    if not password:
                        password = getpass.getpass()
                        password2 = getpass.getpass('Password (again): ')
                        if password != password2:
                            sys.stderr.write("Error: Your passwords didn't match.\n")
                            password = None
                            continue
                    if password.strip() == '':
                        sys.stderr.write("Error: Blank passwords aren't allowed.\n")
                        password = None
                        continue
                    break
            except KeyboardInterrupt:
                sys.stderr.write("\nOperation cancelled.\n")
                sys.exit(1)

        standard_group = Group.objects.get(name="standarduser")

        user = User.objects.create_user(username, email, password)
        user.is_staff = True
        user.groups.add(standard_group)
        user.save()

        userProfile = models.UserProfile(user=user)
        userProfile.save()

        print "remotefsys=%s" % remotefsys

        # Setup the schema for user configuration information (kept in profile)
        self.PARAMS = {'userinfo1': 'param1val',
            'userinfo2': 42,
            'fsys': remotefsys,
            'nci_user': 'root',
            'nci_password': 'changemepassword',  # NB: change this password
            'nci_host': '127.0.0.1',
            'PASSWORD': 'changemepassword',   # NB: change this password
            'USER_NAME': 'root',
            'PRIVATE_KEY': '',
            'PRIVATE_KEY_NAME': '',
            'PRIVATE_KEY_NECTAR': '',
            'PRIVATE_KEY_NCI': '',
            'EC2_ACCESS_KEY': '',
            'EC2_SECRET_KEY': ''
            }

        user_schema = models.Schema.objects.get(namespace=models.UserProfile.PROFILE_SCHEMA_NS)

        param_set, _ = models.UserProfileParameterSet.objects.get_or_create(user_profile=userProfile,
            schema=user_schema)

        for k, v in self.PARAMS.items():
            param_name = models.ParameterName.objects.get(schema=user_schema,
                name=k)
            models.UserProfileParameter.objects.get_or_create(name=param_name,
                paramset=param_set,
                value=v)



         # # Setup the schema for user configuration information (kept in profile)
         # self.PARAMS = {'userinfo1': 'param1val',
         #     'userinfo2': 42,
         #     'fsys': self.remote_fs_path,
         #     'nci_user': 'root',
         #     'nci_password': 'dtofaam',
         #     'nci_host': '127.0.0.1',
         #     }

        # self.PARAMTYPE = {}
        # sch = models.Schema.objects.get(namespace="http://www.rmit.edu.au/user/profile/1")
        # #paramtype = schema_data['http://www.rmit.edu.au/user/profile/1'][1]
        # param_set = models.UserProfileParameterSet.objects.create(user_profile=profile,
        #     schema=sch)
        # for k, v in self.PARAMS.items():
        #     param_name = models.ParameterName.objects.get(schema=sch,
        #         name=k)
        #     models.UserProfileParameter.objects.create(name=param_name,
        #         paramset=param_set,
        #         value=v)



        if verbosity >= 1:
          self.stdout.write("BDPHPCProvider user created successfully.\n")