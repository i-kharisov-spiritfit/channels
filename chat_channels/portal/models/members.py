from main.models.members import Member
from django.db import models

class prtl_Operator(Member):
    portal_user_id = models.IntegerField('ID на портале', unique=True, null=False, blank=False)