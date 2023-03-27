"""
    Title: Webhook Event handler
    Description:
        The class will handle posting webhook events to the client and create necessary verification headers such as,
        hmac signature, account number, and topic. The last part is to post the details to the registared url.
    Created: July 13, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import datetime
import holidays


class DateUtility:
    _default_date = datetime.datetime(year=1, month=1, day=1).replace(microsecond=0, second=0, minute=0, hour=0)
    _saturday = 5
    _sunday = 6
    _one_day = 1
    _two_day = 2

    def __init__(self, pickup: dict = None):
        self._pickup = pickup

        try:
            if self._pickup:
                self._pickup_date = datetime.datetime.strptime(self._pickup["date"], "%Y-%m-%d").replace(microsecond=0)
            else:
                self._pickup_date = datetime.datetime.now().replace(microsecond=0, second=0, minute=0, hour=0)
        except Exception:
            self._pickup_date = datetime.datetime.now().replace(microsecond=0, second=0, minute=0, hour=0)

    def get_estimated_delivery(self, transit: int, country: str, province: str) -> tuple:
        """
            Get estimated delivery date for transit time and account for weekends and holidays for the country passed
            in.
            :param transit: Transit Tine: 1
            :param country: Country Code: CA
            :param province: Province: AB
            :return: Estimated delivery date in iso and transit time.
        """
        country_holidays = holidays.CountryHoliday(country, prov=province, state=province)

        if transit == -1:
            return self._default_date.isoformat(), transit

        transit_loop = transit
        estimated = self._pickup_date

        for i in range(transit_loop):
            estimated = estimated + datetime.timedelta(days=self._one_day)

            if estimated in country_holidays:
                transit += self._one_day
                estimated = estimated + datetime.timedelta(days=self._one_day)

            if estimated.weekday() == self._saturday:
                estimated = estimated + datetime.timedelta(days=self._two_day)
            elif estimated.weekday() == self._sunday:
                estimated = estimated + datetime.timedelta(days=self._one_day)

            if estimated in country_holidays:
                transit += self._one_day
                estimated = estimated + datetime.timedelta(days=self._one_day)

        return estimated.replace(microsecond=0).isoformat(), transit

    def next_business_day(self, country_code: str, prov_code: str, in_date: datetime.date) -> str:
        """
            Get the next business day for the passed in date. Also check for holidays for the country which the pickup
            is in.
            :param country_code: Country Code: CA
            :param prov_code: Province or Region code: AB
            :param in_date: String Date: 2021-01-01
            :return: Next business day in string: 2021-01-01
        """

        country_holidays = holidays.CountryHoliday(country_code, prov=prov_code, state=prov_code)
        one_day = datetime.timedelta(days=self._one_day)
        return_date = in_date + one_day

        if return_date in country_holidays:
            return_date += one_day

        if return_date.weekday() == self._saturday:
            return_date += datetime.timedelta(days=self._two_day)
        elif return_date.weekday() == self._sunday:
            return_date += one_day

        if return_date in country_holidays:
            return_date += one_day

        return return_date.strftime("%Y-%m-%d")

    def new_next_business_day(self, country_code: str, prov_code: str, in_date: datetime) -> datetime:
        """
            Get the next business day for the passed in date. Also check for holidays for the country which the pickup
            is in.
            :param country_code: Country Code: CA
            :param prov_code: Province or Region code: AB
            :param in_date: String Date: 2021-01-01
            :return: Next business day in string: 2021-01-01
        """

        country_holidays = holidays.CountryHoliday(country_code, prov=prov_code, state=prov_code)
        one_day = datetime.timedelta(days=self._one_day)
        return_date = copy.deepcopy(in_date) + one_day

        if return_date in country_holidays:
            return_date += one_day

        if return_date.weekday() == self._saturday:
            return_date += datetime.timedelta(days=self._two_day)
        elif return_date.weekday() == self._sunday:
            return_date += one_day

        if return_date in country_holidays:
            return_date += one_day

        return return_date
