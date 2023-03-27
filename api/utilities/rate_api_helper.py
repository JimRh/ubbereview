
class RateApiHelper:

    @staticmethod
    def split_list(full_list):
        half = len(full_list) // 2
        return full_list[:half], full_list[half:]

    def ubbe_rate_format(self, rates: list):

        sorted_cost = []
        sorted_transit = []

        for rate in rates:
            for middle in rate.get("middle", []):
                middle["carrier_id"] = rate["carrier_id"]
                sorted_cost.append(middle)

                if middle["transit_days"] != "0.00" and int(middle["transit_days"]) != -1:
                    sorted_transit.append(middle)

        sorted_cost_list = sorted(sorted_cost, key=lambda k: k["total"])
        sorted_transit_list = sorted(sorted_transit, key=lambda k: (int(k["transit_days"]), k["total"]))

        l1, l2 = self.split_list(sorted_cost_list)

        cheap_rate = sorted_cost_list[0] if sorted_cost_list else {}
        average_rate = l1[-1] if l1 else {}
        fast_rate = sorted_transit_list[0] if sorted_transit_list else {}

        return {
            "economy": cheap_rate,
            "standard": average_rate,
            "express": fast_rate,
        }
