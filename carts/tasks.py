from celery import shared_task
from django.utils import timezone

from carts.models import Cart, ServerSetting

@shared_task
def kill_old_carts():
    """ will kill all carts that are too old by running kill() on them """
    try:
        life_span: int = ServerSetting.objects.get(name='cart_life_span')
    except ServerSetting.DoesNotExist:
        life_span: int = 30  # in minutes

    old_carts = Cart.objects.filter(is_dead=False, updated__lt=timezone.now()-timezone.timedelta(minutes=life_span))
    for cart in old_carts:
        try:
            cart.kill()
        except Exception as e:
            # Do some logging or admin informing
            pass
