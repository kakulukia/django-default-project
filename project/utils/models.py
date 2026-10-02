from django.db import models
from django.utils.translation import gettext_lazy as _


# base model with useful stuff
##########################################
class BaseModel(models.Model):
    created = models.DateTimeField(_("created"), auto_now_add=True, editable=False, db_index=True)
    modified = models.DateTimeField(auto_now=True, editable=False)

    # access non deleted data only
    data = models.Manager()
    # fallback for 3rd party libs not respecting the default manager
    objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ["-created"]
        get_latest_by = "created"
        base_manager_name = "data"
        default_manager_name = "data"
