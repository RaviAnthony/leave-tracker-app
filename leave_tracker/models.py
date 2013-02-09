#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.db.models.signals import post_save, pre_save
from django.core.mail import send_mail
from django.conf import settings


class LeaveCategory(models.Model):

    type_of_leave = models.CharField(max_length=20)
    number_of_days = models.IntegerField(max_length=10)

    class Meta:
        verbose_name_plural = "Leave Categories"

    def __unicode__(self):
        return self.type_of_leave


class UserProfile(models.Model):

    user = models.OneToOneField(User)
    leaves_taken = models.PositiveIntegerField(max_length=10)
    total_leaves = models.PositiveIntegerField(max_length=10)

    def __unicode__(self):
        return self.user.username

    def user_display(self):
        if self.user.first_name and self.user.last_name:
            return "%s %s" % (self.user.first_name, self.user.last_name)
        elif self.user.first_name:
            return self.user.first_name
        elif self.user.last_name:
            return self.user.last_name
        else:
            return self.user.username


def create_user_profile(sender, **kwargs):
    instance = kwargs['instance']
    if kwargs['created']:
        UserProfile.objects.create(user=instance, leaves_taken=0,
                                   total_leaves=settings.LEAVE_CONST)


post_save.connect(create_user_profile, sender=User)


class LeaveApplication(models.Model):

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    usr = models.ForeignKey(UserProfile)
    leave_category = models.ForeignKey("LeaveCategory")
    status = models.BooleanField()
    subject = models.TextField()

    def __unicode__(self):
        return '%s %s' % (self.usr, self.start_date)



def send_approval_mail(sender, **kwargs):
    instance = kwargs['instance']
    recipients = \
        list(User.objects.filter(is_superuser=True).values_list('email'
             , flat=True))
    subject = ''
    email_body = \
        """Starting %s 
                  Ending %s
                  %s""" \
        % (instance.start_date, instance.end_date, instance.subject)
    if kwargs['created']:
        subject = 'Leave Created by %s' % instance.usr.user
        recipients.append(instance.usr.user.email)
        send_mail(subject, email_body, settings.DEFAULT_FROM_EMAIL, recipients,
                fail_silently=False)
    if instance.status:
        subject = 'Leave Approved for %s' % instance.usr.user
        recipients.append(instance.usr.user.email)
        send_mail(subject, email_body, settings.DEFAULT_FROM_EMAIL, recipients,
                fail_silently=False)


def modify_leave_count(sender, **kwargs):
    instance = kwargs['instance']
    leaves = LeaveApplication.objects.filter(usr=instance.usr, status=True)
    leave_count = 0
    for key in leaves:
        leave_count += (key.end_date - key.start_date).days + 1
    UserProfile.objects.filter(user=instance.usr).update(leaves_taken=leave_count)



post_save.connect(send_approval_mail, sender=LeaveApplication)
post_save.connect(modify_leave_count, sender=LeaveApplication)

def change_username(sender, **kwargs):
    instance = kwargs['instance']
    if instance.username[0:6] == 'openid':
        instance.username = instance.email[0:-11]

pre_save.connect(change_username, sender=User)
