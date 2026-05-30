from django.db import models
from django.contrib.auth.models import User


class AdminLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('ban', 'Banned User'),
        ('unban', 'Unbanned User'),
        ('impersonate', 'Impersonated User'),
        ('order_status', 'Changed Order Status'),
    ]

    admin = models.ForeignKey(User, related_name='admin_actions', on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_model = models.CharField(max_length=50)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin} — {self.action} on {self.target_model} #{self.target_id}"
