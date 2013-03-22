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
import logging.config

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage


logger = logging.getLogger(__name__)


# This stage doesn't do any thing except register its execution
class NullStage(Stage):
    def __init__(self, user_settings=None):
        pass

    def triggered(self, context):
        """
        Return true if the directory pattern triggers this stage, or there
        has been any other error
        """
        # Remember: context is immutable in triggered
        #FIXME: triggered should make deep copy of context to ensure that it is not modified.
        # FIXME: Need to verify that triggered is idempotent.
        logger.debug("Null Stage Triggered?")
        logger.debug("context=%s" % context)

        if self._exists(context, 'http://rmit.edu.au/schemas/stages/null/testing', 'output'):
            self.val = context['http://rmit.edu.au/schemas/stages/null/testing']['output']
        else:
            self.val = 0

        # null_number indicates which of a set of identical nullstages in
        # a composite have been triggered.  It is must be set via passed
        # directive argument.  FIXME: this should be a smart connector specific
        # parameter set during directive definition.

        if self._exists(context, 'http://rmit.edu.au/schemas/stages/null/testing', 'index'):
            self.null_index = context['http://rmit.edu.au/schemas/stages/null/testing']['index']
        else:
            self.null_index = context['http://rmit.edu.au/schemas/smartconnector1/create']['null_number']
            logger.debug("found null_number=%s" % self.null_index)
        if self.null_index:
            return True

        return False

    def process(self, context):
        """ perfrom the stage operation
        """
        #logger.debug("context=%s" % context)
        logger.debug("Null Stage Processing")

    def output(self, context):
        """ produce the resulting datfiles and metadata
        """
        logger.debug("Null Stage Output")

        if not self._exists(context, 'http://rmit.edu.au/schemas/stages/null/testing'):
            context['http://rmit.edu.au/schemas/stages/null/testing'] = {}

        self.val += 1
        context['http://rmit.edu.au/schemas/stages/null/testing']['output'] = self.val

        self.null_index -= 1
        context['http://rmit.edu.au/schemas/stages/null/testing']['index'] = self.null_index

        logger.debug("context=%s" % context)

        return context
