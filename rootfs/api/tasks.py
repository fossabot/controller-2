# Create your tasks here
import time
import uuid
import logging
from datetime import timedelta
from typing import List, Dict
from django.core import signals
from django.utils.timezone import now
from celery import shared_task

from api import manager
from api.models.resource import Resource
logger = logging.getLogger(__name__)


@shared_task
def retrieve_resource(resource):
    task_id = uuid.uuid4().hex
    signals.request_started.send(sender=task_id)
    try:
        if not resource.retrieve():
            t = time.time() - resource.created.timestamp()
            if t < 3600:
                retrieve_resource.apply_async(
                    args=(resource, ),
                    eta=now() + timedelta(seconds=30))
            elif t < 3600 * 12:
                retrieve_resource.apply_async(
                    args=(resource, ),
                    eta=now() + timedelta(seconds=1800))
            else:
                resource.detach_resource()
    except Resource.DoesNotExist:
        logger.exception("retrieve task not found resource: {}".format(resource.id))  # noqa
    finally:
        signals.request_finished.send(sender=task_id)


@shared_task
def measure_config(config: List[Dict[str, str]]):
    task_id = uuid.uuid4().hex
    signals.request_started.send(sender=task_id)
    try:
        measurement = manager.Measurement()
        measurement.post_config(config)
    except Exception as e:
        logger.exception("write influxdb point fail: {}".format(e))
    finally:
        signals.request_finished.send(sender=task_id)


@shared_task
def measure_volumes(volumes: List[Dict[str, str]]):
    task_id = uuid.uuid4().hex
    signals.request_started.send(sender=task_id)
    try:
        measurement = manager.Measurement()
        measurement.post_volumes(volumes)
    except Exception as e:
        logger.exception("write influxdb point fail: {}".format(e))
    finally:
        signals.request_finished.send(sender=task_id)


@shared_task
def measure_networks(networks: List[Dict[str, str]]):
    task_id = uuid.uuid4().hex
    signals.request_started.send(sender=task_id)
    try:
        measurement = manager.Measurement()
        measurement.post_networks(networks)
    except Exception as e:
        logger.exception("write influxdb point fail: {}".format(e))
    finally:
        signals.request_finished.send(sender=task_id)


@shared_task
def measure_instances(instances: List[Dict[str, str]]):
    task_id = uuid.uuid4().hex
    signals.request_started.send(sender=task_id)
    try:
        measurement = manager.Measurement()
        measurement.post_instances(instances)
    except Exception as e:
        logger.exception("write influxdb point fail: {}".format(e))
    finally:
        signals.request_finished.send(sender=task_id)


@shared_task
def measure_resources(resources: List[Dict[str, str]]):
    task_id = uuid.uuid4().hex
    signals.request_started.send(sender=task_id)
    try:
        measurement = manager.Measurement()
        measurement.post_resources(resources)
    except Exception as e:
        logger.exception("write influxdb point fail: {}".format(e))
    finally:
        signals.request_finished.send(sender=task_id)
