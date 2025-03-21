import logging
from django.db import models
from django.db import transaction

from rest_framework.exceptions import NotFound
from django.contrib.auth import get_user_model
from api.utils import dict_diff
from api.exceptions import DryccException, AlreadyExists, UnprocessableEntity
from .base import UuidAuditedModel

User = get_user_model()


class AppSettings(UuidAuditedModel):
    """
    Instance of Application settings used by scheduler
    """

    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    app = models.ForeignKey('App', on_delete=models.CASCADE)
    routable = models.BooleanField(null=True)
    # the default values is None to differentiate from user sending an empty allowlist
    # and user just updating other fields meaning the values needs to be copied from prev release
    allowlist = models.JSONField(default=None, null=True)
    autoscale = models.JSONField(default=dict, blank=True)
    label = models.JSONField(default=dict, blank=True)

    class Meta:
        get_latest_by = 'created'
        unique_together = (('app', 'uuid'), )
        ordering = ['-created']

    def __init__(self, *args, **kwargs):
        UuidAuditedModel.__init__(self, *args, **kwargs)
        self.summary = []

    def __str__(self):
        return "{}-{}".format(self.app.id, str(self.uuid)[:7])

    def new(self, user, allowlist):
        """
        Create a new application appSettings using the provided allowlist
        on behalf of a user.
        """

        app_settings = AppSettings.objects.create(
            owner=user, app=self.app, allowlist=allowlist)

        return app_settings

    def _update_routable(self, previous_settings):
        old = getattr(previous_settings, 'routable', None)
        new = getattr(self, 'routable', None)
        # If no previous settings then assume it is the first record and default to true
        if previous_settings is None:
            setattr(self, 'routable', True)
            self.app.routable(True)
        # if nothing changed copy the settings from previous
        elif new is None and old is not None:
            setattr(self, 'routable', old)
        elif old != new:
            self.app.routable(new)
            self.summary += ["{} changed routablity from {} to {}".format(self.owner, old, new)]

    def _update_allowlist(self, previous_settings):
        # If no previous settings then assume it is the first record and set as empty
        # to prevent from database constraint violation
        if not previous_settings:
            setattr(self, 'allowlist', [])
        old = getattr(previous_settings, 'allowlist', [])
        new = getattr(self, 'allowlist', None)
        # if nothing changed copy the settings from previous
        if new is None and old is not None:
            setattr(self, 'allowlist', old)
        elif set(old) != set(new):
            added = ', '.join(k for k in set(new)-set(old))
            added = 'added ' + added if added else ''
            deleted = ', '.join(k for k in set(old)-set(new))
            deleted = 'deleted ' + deleted if deleted else ''
            changes = ', '.join(i for i in (added, deleted) if i)
            if changes:
                if self.summary:
                    self.summary += ' and '
                self.summary += "{} {}".format(self.owner, changes)

    def _update_autoscale(self, previous_settings):
        data = getattr(previous_settings, 'autoscale', {}).copy()
        new = getattr(self, 'autoscale', {}).copy()
        # If no previous settings then do nothing
        if not previous_settings:
            return

        # if nothing changed copy the settings from previous
        if not new and data:
            setattr(self, 'autoscale', data)
        elif data != new:
            for proc, scale in new.items():
                if scale is None:
                    # error if unsetting non-existing key
                    if proc not in data:
                        raise UnprocessableEntity('{} does not exist under {}'.format(proc, 'autoscale'))  # noqa
                    del data[proc]
                else:
                    data[proc] = scale
            setattr(self, 'autoscale', data)

            # only apply new items
            for proc, scale in new.items():
                self.app.autoscale(proc, scale)

            # if the autoscale information changed, log the dict diff
            changes = []
            old_autoscale = getattr(previous_settings, 'autoscale', {})
            diff = dict_diff(self.autoscale, old_autoscale)
            # try to be as succinct as possible
            added = ', '.join(list(map(lambda x: 'default' if x == '' else x, [k for k in diff.get('added', {})])))  # noqa
            added = 'added autoscale for process type ' + added if added else ''
            changed = ', '.join(list(map(lambda x: 'default' if x == '' else x, [k for k in diff.get('changed', {})])))  # noqa
            changed = 'changed autoscale for process type ' + changed if changed else ''
            deleted = ', '.join(list(map(lambda x: 'default' if x == '' else x, [k for k in diff.get('deleted', {})])))  # noqa
            deleted = 'deleted autoscale for process type ' + deleted if deleted else ''
            changes = ', '.join(i for i in (added, changed, deleted) if i)
            if changes:
                self.summary += ["{} {}".format(self.owner, changes)]

    def _update_label(self, previous_settings):
        data = getattr(previous_settings, 'label', {}).copy()
        new = getattr(self, 'label', {}).copy()
        if not previous_settings:
            return

        # if nothing changed copy the settings from previous
        if not new and data:
            setattr(self, 'label', data)
        elif data != new:
            for k, v in new.items():
                if v is not None:
                    data[k] = v
                else:
                    if k not in data:
                        raise UnprocessableEntity('{} does not exist under {}'.format(k, 'label'))  # noqa
                    del data[k]
            setattr(self, 'label', data)

            diff = dict_diff(self.label, getattr(previous_settings, 'label', {}))
            added = ', '.join(list(map(lambda x: 'default' if x == '' else x, [k for k in diff.get('added', {})])))  # noqa
            added = 'added label ' + added if added else ''
            changed = ', '.join(list(map(lambda x: 'default' if x == '' else x, [k for k in diff.get('changed', {})])))  # noqa
            changed = 'changed label ' + changed if changed else ''
            deleted = ', '.join(list(map(lambda x: 'default' if x == '' else x, [k for k in diff.get('deleted', {})])))  # noqa
            deleted = 'deleted label ' + deleted if deleted else ''
            changes = ', '.join(i for i in (added, changed, deleted) if i)
            if changes:
                if self.summary:
                    self.summary += ' and '
                self.summary += ["{} {}".format(self.owner, changes)]

    @transaction.atomic
    def save(self, *args, **kwargs):
        previous_settings = None
        try:
            previous_settings = self.app.appsettings_set.latest()
        except AppSettings.DoesNotExist:
            pass

        try:
            self._update_routable(previous_settings)
            self._update_allowlist(previous_settings)
            self._update_autoscale(previous_settings)
            self._update_label(previous_settings)
        except (UnprocessableEntity, NotFound):
            raise
        except Exception as e:
            self.delete()
            raise DryccException(str(e)) from e

        if not self.summary and previous_settings:
            self.delete()
            raise AlreadyExists("{} changed nothing".format(self.owner))
        summary = ' '.join(self.summary)
        self.app.log('summary of app setting changes: {}'.format(summary), logging.DEBUG)
        super(AppSettings, self).save(**kwargs)
        self.app.refresh()
