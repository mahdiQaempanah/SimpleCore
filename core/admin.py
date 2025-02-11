from django.contrib import admin

import core.models
#
admin.site.register(core.models.Trade)
admin.site.register(core.models.Market)
admin.site.register(core.models.Order)
