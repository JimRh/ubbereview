from django.contrib.admin import ModelAdmin, register

from api.models import Carrier, Address, Airbase, Account, Contact, \
    Shipment, Leg, ShipDocument, ProBillNumber, FuelSurcharge, CityNameAlias, NorthernPDAddress, \
    Country, Province, TrackingStatus, API, RateSheet, RateSheetLane, Tax, \
    Package, CarrierService, DangerousGood, DangerousGoodPackingGroup, DangerousGoodClassification, \
    DangerousGoodPlacard, DangerousGoodPackagingType, DangerousGoodGenericLabel, DangerousGoodExceptedQuantity, \
    DangerousGoodGroundSpecialProvision, DangerousGoodAirSpecialProvision, Airport, Surcharge, CarrierOption, \
    MandatoryOption, OptionName, DangerousGoodAirCutoff, DangerousGoodPackingInstruction, SubAccount, CarrierAccount, \
    Markup, CarrierMarkup, SkylineAccount, NatureOfGood, SealiftSailingDates, Port, Commodity, \
    BBECityAlias, Dispatch, BillOfLading, BBELane, MarkupHistory, MetricGoals, PackageType, MiddleLocation, \
    LocationDistance, LocationCityAlias, UbbeMlRegressors, RateLog, TransitTime, Webhook, CarrierPickupRestriction, \
    City, MetricAccount, CNInterline, ErrorCode, AccountTier, ApiPermissions, SavedBroker, PromoCode, Transaction, \
    ShipmentDocument, UserTier, ExchangeRate, SavedPackage

from api.models.carrier_markup_history import CarrierMarkupHistory


@register(Account)
class AccountsAdmin(ModelAdmin):
    list_display = ("user",)
    autocomplete_fields = ("user",)
    search_fields = ("user",)

    def get_queryset(self, request):
        qs = super(AccountsAdmin, self).get_queryset(request)
        return qs.select_related("user")


@register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ("address", "city", "province", "postal_code", "has_shipping_bays")
    list_filter = ("has_shipping_bays",)
    search_fields = ("address", "city", "province__name", "postal_code")
    autocomplete_fields = ("province",)

    def get_queryset(self, request):
        qs = super(AddressAdmin, self).get_queryset(request)
        return qs.select_related("province__country")


@register(Airbase)
class AirbaseAdmin(ModelAdmin):
    list_display = ("code", "carrier", "address")
    list_filter = ("carrier",)
    autocomplete_fields = ("address", "carrier")

    def get_queryset(self, request):
        qs = super(AirbaseAdmin, self).get_queryset(request)
        return qs.select_related("address__province__country", "carrier")


@register(Airport)
class AirportAdmin(ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code",)

    def get_queryset(self, request):
        qs = super(AirportAdmin, self).get_queryset(request)
        return qs.select_related("address__province__country")


@register(API)
class APIAdmin(ModelAdmin):
    list_display = ("name", "active")
    list_filter = ("active",)
    actions = ("set_active", "set_inactive")

    def set_active(self, request, queryset):
        queryset.update(active=True)

    def set_inactive(self, request, queryset):
        queryset.update(active=False)

    set_active.short_description = "Set Active"
    set_inactive.short_description = "Set Inactive"


@register(CarrierOption)
class CarrierOptionAdmin(ModelAdmin):
    list_display = (
        "option",
        "carrier",
        "evaluation_expression",
        "minimum_value",
        "maximum_value",
        "start_date",
        "end_date"
    )
    list_filter = ("option", "carrier")
    search_fields = ("option",)
    autocomplete_fields = ("option", "carrier")


@register(Carrier)
class CarrierAdmin(ModelAdmin):
    list_display = (
        "name",
        "code",
        "bc_vendor_code",
        "mode",
        "type",
        "is_kilogram",
        "is_dangerous_good",
        "is_bbe_only",
        "is_allowed_account",
        "is_allowed_public"
    )
    list_filter = ("type", "is_kilogram", "is_dangerous_good", "is_bbe_only", "is_allowed_account", "is_allowed_public")
    search_fields = ("name", "code", "bc_vendor_code")


@register(CarrierService)
class CarrierServiceAdmin(ModelAdmin):
    list_display = ("carrier", "name", "code", "service_days", "description", "exceptions", "is_international")
    list_filter = ("carrier", "is_international")
    search_fields = ("name", "code")
    autocomplete_fields = ("carrier",)


@register(City)
class CityAdmin(ModelAdmin):
    list_display = (
        "name",
        "province",
        "timezone",
        "latitude",
        "longitude",
        "airport_code",
        "has_airport",
        "has_port"
    )
    list_filter = ("has_airport", "has_port")
    search_fields = (
        "name",
        "timezone",
        "province__code",
        "province__country__code",
        "latitude",
        "longitude",
        "airport_code",
        "airport_name",
        "timezone_name",
        "google_place_id"
    )
    autocomplete_fields = ("province", "airport_address")

    def get_queryset(self, request):
        qs = super(CityAdmin, self).get_queryset(request)
        return qs.select_related("province__country", "airport_address__province__country")


@register(CityNameAlias)
class CityNameAliasAdmin(ModelAdmin):
    list_display = ("carrier", "name", "alias", "province")
    list_filter = ("carrier",)
    autocomplete_fields = ("carrier", "province",)


@register(CarrierPickupRestriction)
class CarrierPickupRestrictionAdmin(ModelAdmin):
    list_display = (
        "carrier",
        "min_start_time",
        "max_start_time",
        "min_end_time",
        "max_end_time",
        "pickup_window",
        "min_time_same_day",
        "max_pickup_days"
    )
    list_filter = ("carrier",)
    autocomplete_fields = ("carrier", )


@register(Contact)
class ContactAdmin(ModelAdmin):
    list_display = ("name", "company_name", "phone", "email")
    list_filter = ("company_name",)
    search_fields = ("name", "company_name")


@register(Country)
class CountryAdmin(ModelAdmin):
    list_display = ("name", "code", "currency_code", "currency_name", "_iata_name")
    list_filter = ("currency_name",)


@register(Commodity)
class CommodityAdmin(ModelAdmin):
    list_display = ("shipment", "package", "description", "total_weight", "unit_value", "country_code")


@register(DangerousGood)
class DangerousGoodAdmin(ModelAdmin):
    list_display = (
        "un_number",
        "state",
        "short_proper_shipping_name",
        "classification",
        "packing_group",
        "excepted_quantity",
        "unit_measure",
        "ground_limited_quantity_cutoff",
        "ground_maximum_quantity_cutoff",
        "is_nos"
    )
    list_filter = (
        "state",
        "classification__classification",
        "classification__division",
        "packing_group__packing_group",
        "excepted_quantity",
        "unit_measure",
        "is_gross_measure",
        "is_nos"
    )
    search_fields = ("un_number",)
    autocomplete_fields = (
        "classification",
        "packing_group",
        "air_special_provisions",
        "ground_special_provisions",
        "subrisks",
        "specialty_label",
        "excepted_quantity"
    )


@register(DangerousGoodAirCutoff)
class DangerousGoodAirCutoffAdmin(ModelAdmin):
    list_display = ("cutoff_value", "packing_instruction", "type")
    list_filter = ("type",)
    search_fields = ("packing_instruction__code",)
    autocomplete_fields = ("packing_instruction",)


@register(DangerousGoodAirSpecialProvision)
class DangerousGoodAirSpecialProvisionAdmin(ModelAdmin):
    readonly_fields = ("code",)
    list_display = ("code", "description")
    list_filter = ("is_non_restricted",)
    search_fields = ("code",)


@register(DangerousGoodClassification)
class DangerousGoodClassificationAdmin(ModelAdmin):
    list_display = ("classification", "division", "class_name", "division_characteristics", "label")
    list_filter = ("classification", "division")
    search_fields = ("classification",)
    autocomplete_fields = ("label",)


@register(DangerousGoodExceptedQuantity)
class DangerousGoodExceptedQuantityAdmin(ModelAdmin):
    list_display = ("excepted_quantity_code", "inner_cutoff_value", "outer_cutoff_value")
    search_fields = ("excepted_quantity_code",)


@register(DangerousGoodGenericLabel)
class DangerousGoodGenericLabelAdmin(ModelAdmin):
    list_display = ("name", "width", "height", "label")
    search_fields = ("name",)


@register(DangerousGoodGroundSpecialProvision)
class DangerousGoodGroundSpecialProvisionAdmin(ModelAdmin):
    list_display = ("code", "description")
    search_fields = ("code",)


@register(DangerousGoodPackingGroup)
class DangerousGoodPackingGroupAdmin(ModelAdmin):
    readonly_fields = ("packing_group", "description")
    list_display = ("packing_group", "description")
    search_fields = ("packing_group",)


@register(DangerousGoodPackingInstruction)
class DangerousGoodPackingInstructionAdmin(ModelAdmin):
    list_display = ("code",)
    search_fields = ("code",)
    autocomplete_fields = ("packaging_types",)


@register(DangerousGoodPackagingType)
class DangerousGoodPackagingTypeAdmin(ModelAdmin):
    list_display = ("material", "packaging_type", "details", "code")
    list_filter = ("material", "packaging_type")
    search_fields = ("material", "packaging_type", "code")


@register(DangerousGoodPlacard)
class DangerousGoodPlacardAdmin(ModelAdmin):
    list_display = ("name", "background_rgb", "font_rgb")
    search_fields = ("name",)


@register(Markup)
class MarkupAdmin(ModelAdmin):
    list_display = ("name", "description", "default_percentage")
    search_fields = ("name", "description")


@register(MarkupHistory)
class MarkupHistoryAdmin(ModelAdmin):
    list_display = ("markup", "change_date", "username", "old_value", "new_value")
    search_fields = ("markup__name", "markup__description", "username")
    autocomplete_fields = ("markup",)

    def get_queryset(self, request):
        qs = super(MarkupHistoryAdmin, self).get_queryset(request)
        return qs.select_related("markup")


@register(CarrierMarkup)
class CarrierMarkupAdmin(ModelAdmin):
    list_display = ("markup", "carrier", "percentage")
    list_filter = ("markup",)
    search_fields = ("markup", "carrier")
    autocomplete_fields = ("markup", "carrier")

    def get_queryset(self, request):
        qs = super(CarrierMarkupAdmin, self).get_queryset(request)
        return qs.select_related("markup")


@register(CarrierMarkupHistory)
class CarrierMarkupHistoryAdmin(ModelAdmin):
    list_display = ("markup", "carrier", "change_date", "username", "old_value", "new_value")
    search_fields = (
        "carrier_markup__carrier__name",
        "carrier_markup__markup__name",
        "carrier_markup__markup__description",
        "username"
    )
    autocomplete_fields = ("carrier_markup",)

    def get_queryset(self, request):
        qs = super(CarrierMarkupHistoryAdmin, self).get_queryset(request)
        return qs.select_related("carrier_markup__carrier", "carrier_markup__markup")


@register(CNInterline)
class CNInterlineAdmin(ModelAdmin):
    list_display = ("origin", "destination", "interline_id", "interline_carrier")
    search_fields = ("origin", "destination", "interline_carrier")


@register(FuelSurcharge)
class FuelSurchargeAdmin(ModelAdmin):
    list_display = (
        "carrier", "ten_thou_under",
        "ten_thou_to_fifty_five_thou", "fifty_five_thou_greater",
        "fuel_type", "updated_date"
    )
    list_filter = ("fuel_type",)
    autocomplete_fields = ("carrier",)


@register(MandatoryOption)
class MandatoryOptionAdmin(ModelAdmin):
    list_display = (
        "option",
        "carrier",
        "evaluation_expression",
        "minimum_value",
        "maximum_value",
        "start_date",
        "end_date"
    )
    list_filter = ("option", "carrier")
    search_fields = ("option",)
    autocomplete_fields = ("option", "carrier")


@register(NorthernPDAddress)
class NorthernPDAddressAdmin(ModelAdmin):
    list_display = ("city_name", "pickup_id", "delivery_id", "price_per_kg", "min_price", "cutoff_weight")


@register(TransitTime)
class TransitTimeAdmin(ModelAdmin):
    list_display = ("origin", "destination", "rate_priority_id", "rate_priority_code", "transit_min", "transit_max")
    search_fields = ("origin", "destination", "rate_priority_code")


@register(Package)
class PackageAdmin(ModelAdmin):
    list_display = (
        "package_id", "shipment",
        "width", "length",
        "height", "weight",
        "quantity", "description",
        "package_type", "is_cooler",
        "is_frozen", "un_number",
        "packing_group",
        "packing_type"
    )
    list_filter = ("package_type", "is_cooler", "is_frozen", "packing_group__packing_group", "packing_type")
    search_fields = ("package_id",)
    autocomplete_fields = ("shipment", "packing_group", "packing_type")


@register(OptionName)
class OptionNameAdmin(ModelAdmin):
    list_display = ("name", "description", "is_mandatory")
    list_filter = ("is_mandatory",)
    search_fields = ("name",)


@register(ProBillNumber)
class ProBillNumberAdmin(ModelAdmin):
    list_display = ("carrier", "probill_number", "available")
    list_filter = ("carrier", "available")


@register(Province)
class ProvinceAdmin(ModelAdmin):
    list_display = ("name", "country", "code")
    list_filter = ("country",)
    search_fields = ("country__name", "name")


@register(RateSheet)
class RateSheetAdmin(ModelAdmin):
    list_display = (
        "sub_account",
        "carrier",
        "expiry_date",
        # "rs_type",
        "service_name",
        "origin_province",
        "destination_province",
        "origin_city",
        "destination_city",
        "minimum_charge",
        "transit_days",
        "cut_off_time",
    )
    list_filter = ("sub_account", "carrier")
    search_fields = ("carrier__name", "service_name", "origin_city", "destination_city")
    autocomplete_fields = ("sub_account", "carrier", "origin_province", "destination_province")

    def get_queryset(self, request):
        qs = super(RateSheetAdmin, self).get_queryset(request)
        return qs.select_related(
            "sub_account",
            "carrier",
            "origin_province__country",
            "destination_province__country"
        )


@register(RateSheetLane)
class RateSheetLaneAdmin(ModelAdmin):
    list_display = ("rate_sheet", "min_value", "max_value", "cost")
    list_filter = ("rate_sheet__carrier",)
    search_fields = ("rate_sheet__origin_city", "rate_sheet__destination_city")
    autocomplete_fields = ("rate_sheet",)


@register(ShipDocument)
class ShipDocumentAdmin(ModelAdmin):
    list_display = ("pk", "leg", "type")
    list_filter = ("type",)
    search_fields = ("leg__leg_id", )

    def get_queryset(self, request):
        qs = super(ShipDocumentAdmin, self).get_queryset(request)
        return qs.select_related(
            "leg__carrier",
            "leg__origin__province__country",
            "leg__destination__province__country"
        )


@register(ShipmentDocument)
class ShipmentDocumentAdmin(ModelAdmin):
    list_display = ("pk", "shipment", "type")
    list_filter = ("type",)

    def get_queryset(self, request):
        qs = super(ShipmentDocumentAdmin, self).get_queryset(request)
        return qs.select_related(
            "shipment",
        )


@register(Leg)
class LegAdmin(ModelAdmin):
    list_display = (
        "ship_date",
        "leg_id",
        "carrier",
        "_origin_city",
        "_destination_city",
        "tracking_identifier",
        "carrier_pickup_identifier",
        "on_hold",
        "is_shipped",
        "is_delivered"
    )
    list_filter = (
        "carrier",
        "type",
        "on_hold",
        "is_dangerous_good",
        "is_shipped",
        "is_delivered"
    )
    search_fields = ("leg_id", "tracking_identifier", "carrier_pickup_identifier")
    autocomplete_fields = ("carrier", "shipment", "origin", "destination")
    date_hierarchy = "ship_date"
    ordering = ('-ship_date',)

    def get_queryset(self, request):
        qs = super(LegAdmin, self).get_queryset(request)
        return qs.select_related(
            "carrier",
            "origin__province__country",
            "destination__province__country"
        )


@register(Shipment)
class ShipmentAdmin(ModelAdmin):
    list_display = (
        "creation_date",
        "shipment_id",
        "ff_number",
        "user",
        "subaccount",
        "username",
        # "email",
        "_origin_city",
        "_destination_city",
        "reference_one",
        # "tax",
        "cost",
        # "markup",
        "is_shipped",
        "is_delivered"
    )
    list_filter = (
        "user",
        "is_food",
        "is_dangerous_good",
        "is_shipped",
        "is_delivered"
    )
    search_fields = (
        "shipment_id",
        "ff_number",
        "purchase_order",
        "reference_one",
        "reference_two",
        "bc_customer_code",
        "bc_customer_name",
        "quote_id",
        "project",
        "username",
        "email"
    )
    autocomplete_fields = (
        "user",
        "sender",
        "receiver",
        "origin",
        "destination",
        "broker_address",
        "broker",
        "billing",
        "payer"
    )
    date_hierarchy = "creation_date"
    ordering = ('-creation_date',)

    def get_queryset(self, request):
        qs = super(ShipmentAdmin, self).get_queryset(request)
        return qs.select_related(
            "user",
            "origin__province__country",
            "destination__province__country",
            "sender",
            "receiver",
            "subaccount__contact",
            "broker_address__province__country",
            "broker"
        )


@register(Surcharge)
class SurchargeAdmin(ModelAdmin):
    list_display = ("leg", "name", "cost", "percentage")
    search_fields = ("leg__leg_id",)


@register(Tax)
class TaxesAdmin(ModelAdmin):
    list_display = ("province", "tax_rate", "expiry")
    autocomplete_fields = ("province",)
    date_hierarchy = "expiry"


@register(TrackingStatus)
class TrackingStatusAdmin(ModelAdmin):

    def get_queryset(self, request):
        qs = super(TrackingStatusAdmin, self).get_queryset(request)
        return qs.select_related("leg__carrier",)

    list_display = ("updated_datetime", "leg", "status", "details", "delivered_datetime", "estimated_delivery_datetime")
    search_fields = ("leg__leg_id", "leg__carrier__name")
    autocomplete_fields = ("leg", )


@register(SubAccount)
class SubAccountAdmin(ModelAdmin):

    def get_queryset(self, request):
        qs = super(SubAccountAdmin, self).get_queryset(request)
        return qs.select_related("client_account", "contact", "address")

    list_display = ('tier', 'system', 'account_name', 'bc_customer_code', 'bc_customer_name', 'bc_type', 'bc_file_owner','contact', 'is_default', 'is_metric_included', 'subaccount_number')
    list_filter = ("client_account", "system")
    autocomplete_fields = ("client_account", "address", "contact", "markup", "tier")
    search_fields = ("subaccount_number", "client_account__user__username")


@register(CarrierAccount)
class CarrierAccountAdmin(ModelAdmin):
    list_display = ('carrier', 'subaccount')
    autocomplete_fields = ("carrier", "subaccount")
    search_fields = ("leg___leg_id",)


@register(SkylineAccount)
class SkylineAccountAdmin(ModelAdmin):
    list_display = ("sub_account", "skyline_account", "customer_id")

    autocomplete_fields = (
        "sub_account",
    )

    search_fields = ("skyline_account", "customer_id")


@register(NatureOfGood)
class NatureOfGoodAdmin(ModelAdmin):
    list_display = ("skyline_account", "rate_priority_id", "rate_priority_code", "rate_priority_description",
                    "nog_id", "nog_description", "nog_type", "is_food")
    list_filter = (
        "skyline_account",
        "rate_priority_id",
        "nog_id"
    )

    autocomplete_fields = (
        "skyline_account",
    )


@register(Port)
class PortAdmin(ModelAdmin):
    list_display = (
        "name",
        "code",
        "address"
    )
    autocomplete_fields = ("address",)
    search_fields = ("address__address", "address__city", "name")

    def get_queryset(self, request):
        qs = super(PortAdmin, self).get_queryset(request)
        return qs.select_related("address")


@register(SealiftSailingDates)
class SealiftSailingDatesAdmin(ModelAdmin):
    list_display = (
        "carrier",
        "name",
        "port",
        "sailing_date",
        "weight_capacity",
        "current_weight"
    )
    autocomplete_fields = ("carrier", "port")
    search_fields = ("carrier__name", "port__name")

    def get_queryset(self, request):
        qs = super(SealiftSailingDatesAdmin, self).get_queryset(request)
        return qs.select_related("carrier", "port")


@register(BBECityAlias)
class BBECityAliasAdmin(ModelAdmin):
    list_display = ("name", "alias", "province")
    search_fields = ("name", "alias", "province")
    autocomplete_fields = ("province",)


@register(Dispatch)
class DispatchAdmin(ModelAdmin):
    list_display = ("carrier_name", "location", "name", "phone", "email", "is_default")
    search_fields = ("carrier", "contact")
    autocomplete_fields = ("carrier", "contact")


@register(BillOfLading)
class BillOfLadingAdmin(ModelAdmin):
    list_display = ("dispatch_carrier", "dispatch_location", "bill_of_lading", "is_available")
    search_fields = ("dispatch",)
    autocomplete_fields = ("dispatch",)


@register(BBELane)
class BBELaneAdmin(ModelAdmin):
    list_display = (
        "carrier",
        "service_name",
        "origin_city",
        "origin_province",
        "origin_postal_code",
        "destination_city",
        "destination_province",
        "destination_postal_code",
        "minimum_charge",
        "weight_break",
        "price_per",
        "transit_days",
        "is_metric",
    )
    list_filter = ("carrier", "service_name", "is_metric")
    search_fields = ("service_name", "origin_city", "destination_city", "origin_postal_code", "destination_postal_code")
    autocomplete_fields = ("carrier", "origin_province", "destination_province")

    def get_queryset(self, request):
        qs = super(BBELaneAdmin, self).get_queryset(request)
        return qs.select_related("carrier", "origin_province", "destination_province")


@register(MetricGoals)
class MetricGoalsAdmin(ModelAdmin):
    list_display = (
        "system",
        "start_date",
        "end_date",
        "name",
        "current",
        "goal",
    )

    list_filter = ("system",)

    date_hierarchy = "start_date"
    ordering = ("system", "start_date", "end_date")


@register(MetricAccount)
class MetricAccountAdmin(ModelAdmin):
    list_display = (
        "creation_date",
        "sub_account",
        "shipments",
        "managed_shipments",
        "quantity",
        "weight",
        "managed_weight",
        "revenue",
        "expense",
        "net_profit",
        "managed_revenue",
        "managed_expense",
        "managed_net_profit",
    )

    list_filter = ("sub_account",)
    date_hierarchy = "creation_date"
    autocomplete_fields = ("sub_account",)
    ordering = ("sub_account", 'creation_date')

    def get_queryset(self, request):
        qs = super(MetricAccountAdmin, self).get_queryset(request)
        return qs.select_related("sub_account__contact")


@register(PackageType)
class PackageTypeAdmin(ModelAdmin):
    list_display = (
        "account",
        "code",
        "name",
        "min_overall_dims",
        "max_overall_dims",
        "min_weight",
        "max_weight",
        "is_common",
        "is_dangerous_good",
        "is_pharma",
        "is_active"
    )

    list_filter = ("account", "is_common", "is_dangerous_good", "is_pharma", "is_active")
    autocomplete_fields = ("account", )
    ordering = ("account", 'name')


@register(MiddleLocation)
class MiddleLocationAdmin(ModelAdmin):
    list_display = (
        "code",
        "address",
        "is_available"
    )
    search_fields = (
        "code",
    )

    list_filter = ("is_available",)
    autocomplete_fields = ("address", )
    ordering = ("code", 'address')


@register(LocationDistance)
class LocationDistanceAdmin(ModelAdmin):
    list_display = (
        "origin_city",
        "origin_province",
        "destination_city",
        "destination_province",
        "distance",
        "duration"
    )
    
    search_fields = (
        "origin_city",
        # "origin_province",
        "destination_city",
        # "destination_province",
    )

    autocomplete_fields = ("origin_province", "destination_province")
    ordering = ("origin_city", 'origin_province')


@register(LocationCityAlias)
class LocationCityAliasAdmin(ModelAdmin):
    list_display = ("name", "alias", "province")
    search_fields = ("name", "alias", "province")
    autocomplete_fields = ("province",)


@register(UbbeMlRegressors)
class UbbeMlRegressorsAdmin(ModelAdmin):
    list_display = (
        "active",
        "lbs_0_500_m",
        "lbs_0_500_b",
        "lbs_500_1000_m",
        "lbs_500_1000_b",
        "lbs_1000_2000_m",
        "lbs_1000_2000_b",
        "lbs_2000_5000_m",
        "lbs_2000_5000_b",
        "lbs_5000_10000_m",
        "lbs_5000_10000_b",
        "lbs_10000_plus_m",
        "lbs_10000_plus_b",
        "min_price_m",
        "min_price_b",
    )


@register(RateLog)
class RateLogAdmin(ModelAdmin):

    list_display = ("rate_date", "sub_account", "origin", "destination", "reference_one", "reference_two")
    search_fields = ("origin", "destination", "reference_one", "reference_two")
    autocomplete_fields = ("sub_account",)
    date_hierarchy = "rate_date"
    ordering = ("-rate_date", )

    def get_queryset(self, request):
        qs = super(RateLogAdmin, self).get_queryset(request)
        return qs.select_related("sub_account__contact")

    def origin(self, instance):
        data = instance.rate_data
        return f'{data["origin"].get("city")}, {data["origin"].get("province")}, {data["origin"].get("country")}'

    def destination(self, instance):
        data = instance.rate_data
        return f'{data["destination"].get("city")}, {data["destination"].get("province")}, {data["destination"].get("country")}'

    def reference_one(self, instance):
        data = instance.rate_data
        return f'{data.get("reference_one", "")}'

    def reference_two(self, instance):
        data = instance.rate_data
        return f'{data.get("reference_two", "")}'


@register(Webhook)
class WebhookAdmin(ModelAdmin):
    list_display = ("sub_account", "event", "url")
    list_filter = ("sub_account", "event", "data_format")
    search_fields = ("event", "url", "data_format")
    autocomplete_fields = ("sub_account",)


@register(ErrorCode)
class ErrorCodeAdmin(ModelAdmin):
    list_display = ("system", "source", "type", "code", "name", "location")
    list_filter = ("system", "source")
    search_fields = ("system", "source", "type", "code", "name")


@register(AccountTier)
class AccountTierAdmin(ModelAdmin):
    list_display = ("name", "base_cost", "user_cost", "shipment_cost", "carrier_cost", "api_requests_per_minute_cost")
    search_fields = ("name", )


@register(ApiPermissions)
class ApiPermissionsAdmin(ModelAdmin):
    list_display = ("name", "permissions", "category", "reason", "is_active", "is_admin")
    list_filter = ("category", )
    search_fields = ("name", )


@register(SavedBroker)
class SavedBrokerAdmin(ModelAdmin):
    list_display = ("sub_account", "contact", "address")
    list_filter = ("sub_account", )
    search_fields = ("contact__company_name", "contact__name")
    autocomplete_fields = ("sub_account", "contact", "address")

    def get_queryset(self, request):
        qs = super(SavedBrokerAdmin, self).get_queryset(request)
        return qs.select_related("sub_account", "contact", "address__province__country")


@register(PromoCode)
class PromoCodeAdmin(ModelAdmin):
    list_display = ("code", "start_date", "end_date", "quantity", "flat_amount", "percentage", "min_shipment_cost", "max_discount", "is_active", "is_bulk", "amount")
    search_fields = ("code", )


@register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ("shipment", "transaction_id", "transaction_number", "complete", "card_type", "transaction_amount", "is_pre_authorized", "is_captured", "is_payment")
    list_filter = ("is_pre_authorized", "is_captured", "is_payment", "card_type")
    search_fields = ("shipment__shipment_id", "transaction_id", "transaction_number", "complete")
    autocomplete_fields = ("shipment", )

    def get_queryset(self, request):
        qs = super(TransactionAdmin, self).get_queryset(request)
        return qs.select_related("shipment")


@register(UserTier)
class UserTierAdmin(ModelAdmin):
    list_display = ("user", "tier",)


@register(ExchangeRate)
class ExchangeRateAdmin(ModelAdmin):
    list_display = ("exchange_rate_date", "expire_date", "source_currency", "target_currency", "exchange_rate")
    search_fields = ("source_currency", "target_currency")


@register(SavedPackage)
class SavedPackageAdmin(ModelAdmin):
    list_display = ("id", "sub_account", "box_type", "package_type", "freight_class_id", "description", "length", "width", "height", "weight")
    list_filter = ("sub_account", "box_type", "package_type", "length", "width", "description", "height", "weight")
    search_fields = ("sub_account", "box_type", "package_type", "length", "width", "description", "height", "weight")
    autocomplete_fields = ("sub_account",)
