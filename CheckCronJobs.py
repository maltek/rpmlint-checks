# vim: sw=4 ts=4 sts=4 et :
#############################################################################
# Author        : Matthias Gerstner
# Purpose       : Enforce Whitelisting for cron jobs in /etc/cron.* directories
#############################################################################

import os

import AbstractCheck
import Config
import Whitelisting

from Filter import addDetails

# this option is found in config files in /opt/testing/share/rpmlint/mini,
# installed there by the rpmlint-mini package.
WHITELIST_DIR = Config.getOption('WhitelistDataDir', [])


class CronCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "CheckCronJobs")

    def _getPrintPrefix(self):
        """Returns a prefix for error / warning output."""
        return self.__class__.__name__ + ":"

    def _getErrorPrefix(self):
        return self._getPrintPrefix() + " ERROR: "

    def _getWarnPrefix(self):
        return self._getPrintPrefix() + " WARN: "

    def check(self, pkg):
        """This is called by rpmlint to perform the cron check on the given
        pkg."""

        for wd in WHITELIST_DIR:
            candidate = os.path.join(wd, "cron-whitelist.json")
            if os.path.exists(candidate):
                whitelist_path = candidate
                break
        else:
            # don't ruin the whole run if this check is not configured, this
            # was hopefully intended by the user.
            return

        parser = Whitelisting.WhitelistParser(whitelist_path)
        whitelist_entries = parser.parse(pkg.name)
        wl_checker = Whitelisting.WhitelistChecker(
            whitelist_entries,
            restricted_paths=(
                "/etc/cron.d/", "/etc/cron.hourly/", "/etc/cron.daily/",
                "/etc/cron.weekly/", "/etc/cron.monthly/"
            ),
            error_map={
                "unauthorized": "cronjob-unauthorized-file",
                "changed": "cronjob-changed-file",
                "ghost": "cronjob-ghost-file"
            }
        )
        wl_checker.check(pkg)


# needs to be instantiated for the check to be registered with rpmlint
check = CronCheck()

for _id, desc in (
        (
            'cronjob-unauthorized-file',
            """A cron job file is installed by this package. If the package is
            intended for inclusion in any SUSE product please open a bug report to request
            review of the package by the security team. Please refer to {url} for more
            information"""
        ),
        (
            'cronjob-changed-file',
            """A cron job or cron job related file installed by this package changed
            in content. Please open a bug report to request follow-up review of the
            introduced changes by the security team. Please refer to {url} for more
            information."""
        ),
        (
            'cronjob-ghost-file',
            """A cron job path has been marked as %ghost file by this package.
            This is not allowed as it is impossible to review. Please refer to
            {url} for more information."""
        )
):
    addDetails(_id, desc.format(url=Whitelisting.AUDIT_BUG_URL))
