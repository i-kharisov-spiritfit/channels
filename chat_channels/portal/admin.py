from django.contrib import admin

# Register your models here.
from .models import prtl_Line, prtl_Operator


class LineAdmin(admin.ModelAdmin):
    # readonly_fields = ["id", "name", "icon"]
    list_display = ("id", "name", "open", "portal_line_id")

    def save_model(self, request, obj:prtl_Line, form, change):
        if not obj.pk:
            obj.install_connector()
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj:prtl_Line):
        obj.uninstall_connector()
        super().delete_model(request, obj)


admin.site.register(prtl_Line, LineAdmin)

class OperatorAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
admin.site.register(prtl_Operator, OperatorAdmin)