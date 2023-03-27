
from django.core.management import BaseCommand

from api.apis.carriers.action_express.action_express_api import ActionExpress
from api.apis.carriers.calm_air.calm_air_api import CalmAirApi
from api.apis.carriers.canada_post.canada_post_api import CanadaPostApi
from api.apis.carriers.cargojet.endpoints.cj_track import CargojetTrack

from api.apis.carriers.day_ross_v2.day_ross_api import DayRossApi
from api.apis.carriers.fedex.fedex_api import FedexApi
from api.apis.carriers.purolator.courier.purolator_api import PurolatorApi
from api.apis.carriers.manitoulin.manitoulin_api import ManitoulinApi
from api.apis.carriers.skyline.skyline_api_v3 import SkylineApi
from api.apis.carriers.tst_cf_express.endpoints.tst_cf_track_v2 import TstCfExpressTrack
from api.apis.carriers.twoship.endpoints.twoship_track_v2 import TwoShipTrack
from api.apis.carriers.yrc.yrc_api import YRCFreight
from api.apis.track.track import Track
from api.background_tasks.business_central import CeleryBusinessCentral
from api.exceptions.project import ViewException, NoTrackingStatus
from api.globals.carriers import CAN_NORTH, TWO_SHIP_CARRIERS, DAY_N_ROSS, TST, CAN_POST, CALM_AIR, PUROLATOR, \
    ACTION_EXPRESS, CARGO_JET, FEDEX, YRC, MANITOULIN
from api.globals.project import LOGGER
from api.models import Leg


class Command(BaseCommand):

    def _old_track(self):
        LOGGER.info("Leg Tracking Start")

        for leg in Leg.get_all_undelivered_legs():
            carrier_code = leg.carrier.code
            shipment = leg.shipment

            if not shipment:
                self.stderr.write(self.style.ERROR('Leg {}: Could not find parent shipment.'.format(leg.leg_id)))
                continue

            if leg.service_code in ["PICK_DEL"]:
                continue

            if carrier_code == CAN_NORTH and leg.tracking_identifier:
                api = SkylineApi(ubbe_request={})
            elif carrier_code in TWO_SHIP_CARRIERS:
                api = TwoShipTrack(ubbe_request={})
            elif carrier_code == DAY_N_ROSS:
                api = DayRossApi(ubbe_request={})
            elif carrier_code == CAN_POST:
                api = CanadaPostApi(ubbe_request={})
            elif carrier_code == TST:
                api = TstCfExpressTrack(ubbe_request={})
            elif carrier_code == CALM_AIR:
                api = CalmAirApi(ubbe_request={})
            elif carrier_code == PUROLATOR:
                api = PurolatorApi(ubbe_request={})
            elif carrier_code == ACTION_EXPRESS:
                api = ActionExpress(ubbe_request={})
            elif carrier_code == CARGO_JET:
                api = CargojetTrack(ubbe_request={})
            elif carrier_code == YRC:
                api = YRCFreight(ubbe_request={})
            elif carrier_code == FEDEX:
                api = FedexApi(ubbe_request={})
            elif carrier_code == MANITOULIN:
                api = ManitoulinApi(ubbe_request={})
            else:
                self.stderr.write(
                    self.style.ERROR('Leg {}: Cannot track with carrier ID {}'.format(leg.leg_id, carrier_code))
                )
                continue

            try:
                latest_status = api.track(leg=leg)
            except ViewException as e:
                self.stderr.write(self.style.ERROR('Leg {}: {}'.format(leg.leg_id, str(e.message))))
                continue
            except NoTrackingStatus as e:
                self.stderr.write(self.style.ERROR('Leg {}: {}'.format(leg.leg_id, str(e))))
                continue
            except Exception as e:
                self.stderr.write(self.style.ERROR('Leg {}: {}'.format(leg.leg_id, str(e))))
                continue

            if latest_status["leg"].is_delivered:
                leg = latest_status["leg"]

                if leg.shipment.ff_number:
                    data = {
                        "job_number": leg.shipment.ff_number,
                        "leg_id": leg.leg_id
                    }

                    CeleryBusinessCentral().deliver_job_file.delay(data=data)

                leg_count = Leg.objects.filter(shipment=leg.shipment).count()
                delivered_leg = Leg.objects.filter(shipment=leg.shipment, is_delivered=True).count()

                if leg_count == delivered_leg:
                    leg.shipment.is_delivered = True
                    leg.shipment.save()

        LOGGER.info("Leg Tracking Complete")

    def handle(self, *args, **options) -> None:

        # self._old_track()

        Track(command=self).track()
