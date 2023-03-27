"""
    Title: ubbe Api V3 Urls
    Description: This file will contain all urls for ubbe api.
    Created: Nov 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.urls import path

from api.views_v3.account_apis import carrier_account_api, saved_broker_api, saved_package_api
from api.views_v3.account_apis import sub_account_api
from api.views_v3.account_apis import account_api
from api.views_v3.account_apis import account_tier_api
from api.views_v3 import bc_apis
from api.views_v3.account_apis.markup_apis import carrier_markup_api
from api.views_v3.account_apis.markup_apis import markup_api
from api.views_v3.admin_apis import airport_api
from api.views_v3.admin_apis import api_apis
from api.views_v3.admin_apis import api_permissions_api
from api.views_v3.admin_apis import distance_api
from api.views_v3.admin_apis import middle_api
from api.views_v3.carrier_apis import airbase_api
from api.views_v3.carrier_apis import bill_of_lading_api
from api.views_v3.carrier_apis import carrier_api
from api.views_v3.carrier_apis import carrier_service_api
from api.views_v3.carrier_apis import city_alias_api
from api.views_v3.carrier_apis import dispatch_api
from api.views_v3.carrier_apis import fuel_surcharge_api
from api.views_v3.dangerous_goods_apis import dg_placard_api
from api.views_v3.dangerous_goods_apis import dg_air_cutoff_api
from api.views_v3.dangerous_goods_apis import dg_air_special_provision_api
from api.views_v3.dangerous_goods_apis import dg_api
from api.views_v3.dangerous_goods_apis import dg_classification_api
from api.views_v3.dangerous_goods_apis import dg_excepted_quantity_api
from api.views_v3.dangerous_goods_apis import dg_generic_label_api
from api.views_v3.dangerous_goods_apis import dg_ground_special_provision_api
from api.views_v3.dangerous_goods_apis import dg_packaging_type_api
from api.views_v3.dangerous_goods_apis import dg_packing_group_api
from api.views_v3.dangerous_goods_apis import dg_packing_instruction_api
from api.views_v3.location_apis import country_api
from api.views_v3.location_apis import province_api
from api.views_v3.location_apis import postal_code_validate_api
from api.views_v3.main_apis import cancel_api, promo_code_api, shipment_document_api
from api.views_v3.main_apis import leg_document_api
from api.views_v3.main_apis import package_types_api
from api.views_v3.main_apis import rate_api
from api.views_v3.main_apis import track_api
from api.views_v3.main_apis import webhook_api
from api.views_v3.main_apis import ship_api
from api.views_v3.main_apis import manual_ship_api
from api.views_v3.metric_apis import accounts_v3_api
from api.views_v3.metric_apis import averages_v3_api
from api.views_v3.metric_apis import carriers_v3_api
from api.views_v3.metric_apis import finance_per_year_v3_api
from api.views_v3.metric_apis import goals_v3_api
from api.views_v3.metric_apis import overview_v3_api
from api.views_v3.metric_apis import routes_v3_api
from api.views_v3.metric_apis import shipment_per_year_v3_api
from api.views_v3.metric_apis import breakdown_v1_api
from api.views_v3.option_apis import mandatory_option_api
from api.views_v3.option_apis import option_api
from api.views_v3.option_apis import optional_option_api
from api.views_v3.pickup_apis import pickup_apis
from api.views_v3.pickup_apis import pickup_restriction_api
from api.views_v3.rate_sheet_apis import rate_sheet_api
from api.views_v3.rate_sheet_apis import rate_sheet_cost_api
from api.views_v3.rate_sheet_apis import rate_sheet_upload_api
from api.views_v3.report_apis import quote_history_report_api, shipment_overview_report_api
from api.views_v3.report_apis import report_api
from api.views_v3.report_apis import account_report_api
from api.views_v3.report_apis import admin_shipment_overview_report_api
from api.views_v3.sea_apis import port_api
from api.views_v3.sea_apis import sailing_date_api
from api.views_v3.shipment_apis import search_shipments_api
from api.views_v3.shipment_apis import leg_api
from api.views_v3.shipment_apis import overdue_api
from api.views_v3.shipment_apis import package_apis
from api.views_v3.shipment_apis import shipment_api
from api.views_v3.shipment_apis import surcharge_api
from api.views_v3.shipment_apis import transaction_api
from api.views_v3.skyline_apis import nature_of_goods_api
from api.views_v3.skyline_apis import cn_transit_time_api
from api.views_v3.skyline_apis import cn_pd_api
from api.views_v3.skyline_apis import cn_interlines_api
from api.views_v3.skyline_apis import cn_skyline_account_api
from api.views_v3.admin_apis import error_code_api
from api.views_v3.admin_apis import exchange_rate_api

urlpatterns = [

    # *****************************************************************************************************
    #                                    Public Apis - ubbe third party clients
    # *****************************************************************************************************

    # Main Apis
    path('rate', rate_api.RateApi.as_view(), name='RateApiV3'),
    path('rate_v3', rate_api.RateV3Api.as_view(), name='RateV3Api'),

    path('ship', ship_api.ShipApi.as_view(), name="ShipApiV3"),
    path('push_leg', ship_api.NextLegPush.as_view(), name='NextLegPushV3'),

    path('options', option_api.OptionsApi.as_view(), name='OptionsApiV3'),
    path('track', track_api.TrackingApi.as_view(), name='TrackingApiV3'),
    path('cancel', cancel_api.CancelApi.as_view(), name='CancelApiV3'),
    path('documents/leg', leg_document_api.LegDocumentApi.as_view(), name='DocumentApiV3'),
    path('documents/leg/<int:pk>', leg_document_api.LegDocumentDetailApi.as_view(), name='DocumentDetailApiV3'),
    path('documents/shipment', shipment_document_api.ShipmentDocumentApi.as_view(), name='ShipmentDocumentApiV3'),
    path('documents/shipment/<int:pk>', shipment_document_api.ShipmentDocumentDetailApi.as_view(),name='ShipmentDocumentDetailApiV3'),

    path('package_types', package_types_api.PackageTypeApi.as_view(), name='PackageTypeApiV3'),

    # Pickup Apis
    path('pickup', pickup_apis.PickupApi.as_view(), name="PickupV3"),
    path('pickup/timezone', pickup_apis.PickupTimezoneApi.as_view(), name="PickupTimezoneApiV3"),
    path('pickup/validate', pickup_apis.PickupValidateApi.as_view(), name="PickupValidateApiV3"),

    # Location Apis
    path('countries', country_api.GetCountries.as_view(), name='GetCountriesV3'),
    path('countries/<str:code>', country_api.CountryDetailApi.as_view(), name='CountryDetailApiV3'),
    path('provinces', province_api.GetProvinces.as_view(), name='GetProvincesV3'),
    path('provinces/<int:pk>', province_api.ProvinceDetailApi.as_view(), name='ProvinceDetailApiV3'),

    path('postal_code/validate', postal_code_validate_api.PostalCodeValidateApi.as_view(), name='PostalCodeValidateApiV3'),

    # Shipment Apis
    path('shipments', shipment_api.ShipmentApi.as_view(), name='ShipmentApiV3'),
    path('shipments/<str:shipment_id>', shipment_api.ShipmentDetailApi.as_view(), name='ShipmentDetailApiV3'),
    path('search_shipments', search_shipments_api.FindShipmentApi.as_view(), name='FindShipmentApiV3'),

    # Leg Apis
    path('legs', leg_api.LegApi.as_view(), name='LegApiV3'),
    path('legs/<str:shipment_id>', leg_api.LegDetailApi.as_view(), name='LegDetailApiV3'),
    path('overdue', overdue_api.LegOverdueApi.as_view(), name='LegOverdueApiV3'),

    # Packages Apis
    path('packages', package_apis.PackageApi.as_view(), name='PackageApiV3'),
    path('packages/<str:shipment_id>', package_apis.PackageDetailApi.as_view(), name='PackageDetailApiV3'),

    # Webhooks
    path('webhooks', webhook_api.WebhookApi.as_view(), name='WebhookApiV3'),
    path('webhooks/<int:pk>', webhook_api.WebhookDetailApi.as_view(), name='WebhookDetailApiV3'),

    # Saved Broker
    path('saved/broker', saved_broker_api.SavedBrokerApi.as_view(), name='SavedBrokerApiV3'),
    path('saved/broker/<int:pk>', saved_broker_api.SavedBrokerDetailApi.as_view(), name='SavedBrokerDetailApiV3'),

    # Saved Package
    path('saved/package', saved_package_api.SavedPackageApi.as_view(), name='SavedPackageApiV3'),
    path('saved/package/<int:pk>', saved_package_api.SavedPackageDetailApi.as_view(), name='SavedPackageDetailApiV3'),
    path('saved/package/upload', saved_package_api.SavedPackageUploadApi.as_view(), name='SavedPackageUploadApiV3'),

    # *****************************************************************************************************
    #                                    Private Apis - BBE Only
    # *****************************************************************************************************

    path('ubbe_rate', rate_api.RateUbbeApi.as_view(), name='RateUbbeApiV3'),

    path('manual_ship', manual_ship_api.ManualShipApi.as_view(), name="ManualShipApiV3"),

    # Surcharge Apis -> Why? These return base cost
    path('surcharges/', surcharge_api.SurchargeApi.as_view(), name='SurchargeApiV3'),
    path('surcharges/<str:leg_id>', surcharge_api.SurchargeDetailApi.as_view(), name='SurchargeDetailApiV3'),

    # Packages Apis
    path('transactions', transaction_api.TransactionApi.as_view(), name='TransactionApiV3'),
    path('transactions/<int:pk>', transaction_api.TransactionDetailApi.as_view(), name='TransactionDetailApiV3'),

    # Options Management Apis
    path('options/names', option_api.OptionNameApi.as_view(), name='OptionNameApiV3'),
    path('options/optional', optional_option_api.OptionalOptionApi.as_view(), name='OptionalOptionApiV3'),
    path('options/mandatory', mandatory_option_api.MandatoryOptionApi.as_view(), name='MandatoryOptionApiV3'),

    # Carrier Apis
    path('carriers', carrier_api.CarrierApi.as_view(), name='CarriersV3'),
    path('carriers/<int:code>', carrier_api.CarrierDetailApi.as_view(), name='CarrierDetailApiV3'),

    path('carrier_services', carrier_service_api.CarrierServiceApi.as_view(), name='CarrierServiceApiV3'),
    path('carrier_services/<int:pk>', carrier_service_api.CarrierServiceDetailApi.as_view(), name='CarrierServiceDetailApiV3'),

    path('fuel_surcharge', fuel_surcharge_api.FuelSurchargeApi.as_view(), name='FuelSurchargeApiV3'),
    path('fuel_surcharge/<int:pk>', fuel_surcharge_api.FuelSurchargeDetailApi.as_view(), name='FuelSurchargeDetailApiV3'),

    path('dispatch', dispatch_api.DispatchApi.as_view(), name='DispatchApiV3'),
    path('dispatch/<int:pk>', dispatch_api.DispatchDetailApi.as_view(), name='DispatchDetailApiV3'),

    path('bill_of_lading', bill_of_lading_api.BillOfLadingApi.as_view(), name='BillOfLadingApiV3'),
    path('bill_of_lading/<int:pk>', bill_of_lading_api.BillOfLadingDetailApi.as_view(), name='BillOfLadingDetailApiV3'),

    path('city_alias', city_alias_api.CityNameAliasApi.as_view(), name='CityNameAliasApiV3'),
    path('city_alias/<int:pk>', city_alias_api.CityNameAliasDetailApi.as_view(), name='CityNameAliasDetailApiV3'),
    path('city_alias_upload', city_alias_api.CarrierCityAliasUploadApi.as_view(), name='CarrierCityAliasUploadApiV3'),

    path('airbase', airbase_api.AirbaseApi.as_view(), name='AirbaseApiV3'),
    path('airbase/<int:pk>', airbase_api.AirbaseDetailApi.as_view(), name='AirbaseDetailApiV3'),

    # Pickup Restrictions
    path('pickup/restrictions', pickup_restriction_api.PickupRestrictionApi.as_view(), name='PickupRestrictionApiV3'),
    path('pickup/restrictions/<int:pk>', pickup_restriction_api.PickupRestrictionDetailApi.as_view(), name='PickupRestrictionDetailApiV3'),

    # Package Types
    path('package_types/<int:pk>', package_types_api.PackageTypeDetailApi.as_view(), name='PackageTypeDetailApiV3'),

    # Account Apis
    path('accounts', account_api.AccountApi.as_view(), name='AccountApiV3'),
    path('accounts/<int:pk>', account_api.AccountDetailApi.as_view(), name='AccountDetailApiV3'),

    path('sub_accounts', sub_account_api.SubAccountApi.as_view(), name='SubAccountApiV3'),
    path('sub_accounts/<int:pk>', sub_account_api.SubAccountDetailApi.as_view(), name='SubAccountDetailApiV3'),

    path('carrier_accounts', carrier_account_api.CarrierAccountApi.as_view(), name='CarrierAccountApiV3'),
    path('carrier_accounts/<int:pk>', carrier_account_api.CarrierAccountDetailApi.as_view(), name='CarrierAccountDetailApiV3'),

    path('tiers', account_tier_api.AccountTierApi.as_view(), name='AccountTierApiV3'),
    path('tiers/<int:pk>', account_tier_api.AccountTierDetailApi.as_view(), name='AccountTierDetailApiV3'),

    # Markup Apis
    path('markups', markup_api.MarkupApi.as_view(), name='MarkupApiV3'),
    path('markups/<int:pk>', markup_api.MarkupDetailApi.as_view(), name='MarkupDetailApiV3'),
    path('markups/<int:pk>/history', markup_api.MarkupHistoryApi.as_view(), name='MarkupHistoryApiV3'),

    path('carrier_markups', carrier_markup_api.CarrierMarkupApi.as_view(), name='CarrierMarkupApiV3'),
    path('carrier_markups/<int:pk>', carrier_markup_api.CarrierMarkupDetailApi.as_view(), name='CarrierMarkupDetailApiV3'),
    path('carrier_markups/<int:pk>/history', carrier_markup_api.CarrierMarkupHistoryApi.as_view(), name='CarrierMarkupHistoryApiV3'),

    # Metric Apis
    path('metrics/overview', overview_v3_api.MetricOverviewApi.as_view(), name='MetricOverviewApiV3'),
    path('metrics/shipments_per_year', shipment_per_year_v3_api.MetricShipmentPerYearApi.as_view(), name='MetricShipmentPerYearApiV3'),
    path('metrics/finance_per_year', finance_per_year_v3_api.MetricFinancePerYearApi.as_view(), name='MetricFinancePerYearApiV3'),
    path('metrics/averages', averages_v3_api.MetricAveragesApi.as_view(), name='MetricAveragesApiV3'),
    path('metrics/routes', routes_v3_api.MetricRoutesApi.as_view(), name='MetricRoutesApiV3'),
    path('metrics/carriers', carriers_v3_api.MetricCarriersApi.as_view(), name='MetricCarriersApiV3'),
    path('metrics/accounts', accounts_v3_api.MetricAccountsApi.as_view(), name='MetricAccountsApiV3'),
    path('metrics/goals', goals_v3_api.MetricGoalsApi.as_view(), name='MetricGoalsApiV3'),
    path('metrics/goals/<int:pk>', goals_v3_api.MetricGoalsDetailApi.as_view(), name='MetricGoalsDetailApiV3'),
    path('metrics/breakdown', breakdown_v1_api.MetricBreakdownApi.as_view(), name='MetricBreakdownApiV1'),

    # Admin Apis
    path('api', api_apis.ApiApi.as_view(), name='ApiApiV3'),
    path('api/<int:pk>', api_apis.ApiDetailApi.as_view(), name='ApiDetailApiV3'),

    path('api_permission', api_permissions_api.ApiPermissionsApi.as_view(), name='ApiPermissionsApiV3'),
    path('api_permission/<int:pk>', api_permissions_api.ApiPermissionsDetailApi.as_view(), name='ApiPermissionsDetailApiV3'),
    path('api_permission/upload', api_permissions_api.ApiPermissionUploadApi.as_view(), name='ApiPermissionUploadApiV3'),

    path('airports', airport_api.AirportApi.as_view(), name='AirportApiV3'),
    path('airports/<int:pk>', airport_api.AirportDetailApi.as_view(), name='AirportDetailApiV3'),

    path('ports', port_api.PortApi.as_view(), name='PortApiV3'),
    path('ports/<int:pk>', port_api.PortDetailApi.as_view(), name='PortDetailApiV3'),

    path('sailing_dates', sailing_date_api.SealiftSailingDatesApi.as_view(), name='SealiftSailingDatesApiV3'),
    path('sailing_dates/<int:pk>', sailing_date_api.SailingDateDetailApi.as_view(), name='SailingDateDetailApiV3'),

    path('exchange_rates', exchange_rate_api.ExchangeRateApi.as_view(), name='ExchangeRateApiV3'),
    path('exchange_rates/<int:pk>', exchange_rate_api.ExchangeRateDetailApi.as_view(), name='ExchangeRateDetailApiV3'),

    # Location Apis
    path('location/interline', middle_api.MiddleLocationApi.as_view(), name='MiddleLocationApiV3'),
    path('location/interline/<int:pk>', middle_api.MiddleLocationDetailApi.as_view(), name='MiddleLocationDetailApiV3'),

    path('location/distance', distance_api.LocationDistanceApi.as_view(), name='LocationDistanceApiV3'),
    path('location/distance/<int:pk>', distance_api.LocationDistanceDetailApi.as_view(), name='LocationDistanceDetailApiV3'),
    path('location/distance_between', distance_api.LocationDistanceBetweenApi.as_view(), name='LocationDistanceBetweenApiV3'),

    # Rate Sheet Apis
    path('rate_sheets/lane', rate_sheet_api.RateSheetApi.as_view(), name='RateSheetApiV3'),
    path('rate_sheets/lane/<int:pk>', rate_sheet_api.RateSheetDetailApi.as_view(), name='RateSheetDetailApiV3'),
    path('rate_sheets/costs', rate_sheet_cost_api.RateSheetLaneApi.as_view(), name='RateSheetLaneApiV3'),
    path('rate_sheets/costs/<int:pk>', rate_sheet_cost_api.RateSheetLaneDetailApi.as_view(), name='RateSheetLaneDetailApiV3'),

    path('rate_sheets/upload', rate_sheet_upload_api.RateSheetUploadApi.as_view(), name='RateSheetUploadApiV3'),

    # Business Central
    path('business_central/customers', bc_apis.BCCustomersApi.as_view(), name='BCCustomersApi31'),
    path('business_central/items', bc_apis.BCItemsApi.as_view(), name='BCItemsApiV3'),
    path('business_central/vendors', bc_apis.BCVendorsApi.as_view(), name='BCVendorsApiV3'),
    path('business_central/job_list', bc_apis.BCJobListApi.as_view(), name='BCJobListApiV3'),

    # Dangerous Goods
    path('dangerous_goods/old_unnumbers', dg_api.DGUNumberInfo.as_view(), name="DGUNumberInfoV3"),
    path('dangerous_goods/unnumbers', dg_api.DangerousGoodApi.as_view(), name="DangerousGoodApiV3"),
    path('dangerous_goods/unnumbers/<int:pk>', dg_api.DangerousGoodDetailApi.as_view(), name="DangerousGoodDetailApiV3"),
    path('dangerous_goods/classifications', dg_classification_api.DangerousGoodClassificationApi.as_view(), name="DangerousGoodClassificationApiV3"),
    path('dangerous_goods/packing_groups', dg_packing_group_api.DangerousGoodPackingGroupApi.as_view(), name="DangerousGoodPackingGroupApiV3"),
    path('dangerous_goods/excepted_quantity', dg_excepted_quantity_api.DangerousGoodExceptedQuantityApi.as_view(), name="DangerousGoodExceptedQuantityApiV3"),
    path('dangerous_goods/air_cutoff', dg_air_cutoff_api.DangerousGoodAirCutoffApi.as_view(), name="DangerousGoodAirCutoffApiV3"),
    path('dangerous_goods/generic_label', dg_generic_label_api.DangerousGoodGenericLabelApi.as_view(), name="DangerousGoodGenericLabelApiV3"),
    path('dangerous_goods/air_special_provision', dg_air_special_provision_api.DangerousGoodAirSpecialProvisionApi.as_view(), name="DangerousGoodAirSpecialProvisionApiV3"),
    path('dangerous_goods/ground_special_provision', dg_ground_special_provision_api.DangerousGoodGroundSpecialProvisionApi.as_view(), name="DangerousGoodGroundSpecialProvisionApiV3"),
    path('dangerous_goods/packing_instructions', dg_packing_instruction_api.DangerousGoodPackingInstructionApi.as_view(), name="DangerousGoodPackingInstructionApiV3"),
    path('dangerous_goods/placards', dg_placard_api.DangerousGoodPlacardApi.as_view(), name="DangerousGoodPlacardApiV3"),

    path('dangerous_goods/packing_types', dg_packaging_type_api.DangerousGoodPackagingTypeApi.as_view(), name="DangerousGoodPackagingTypeApiV3"),

    # Skyline
    path('nature_of_goods', nature_of_goods_api.NatureOfGoodsApi.as_view(), name='NatureOfGoodsApiV3'),

    path('cn/skyline_accounts', cn_skyline_account_api.CNSkylineAccountApi.as_view(), name='CNSkylineAccountApiV3'),
    path('cn/skyline_accounts/<int:pk>', cn_skyline_account_api.CNSkylineAccountDetailApi.as_view(), name='CNSkylineAccountDetailApiV3'),
    path('cn/transit_times', cn_transit_time_api.CNTransitTimeApi.as_view(), name='CNTransitTimeApiV3'),
    path('cn/transit_times/<int:pk>', cn_transit_time_api.CNTransitTimeDetailApi.as_view(), name='CNTransitTimeDetailApiV3'),
    path('cn/pickup_delivery', cn_pd_api.CNNorthernPDAddressApi.as_view(), name='CNNorthernPDAddressApiV3'),
    path('cn/pickup_delivery/<int:pk>', cn_pd_api.CNNorthernPDAddressDetailApi.as_view(), name='CNNorthernPDAddressDetailApiV3'),
    path('cn/interline', cn_interlines_api.CNInterlineApi.as_view(), name='CNInterlineApiV3'),
    path('cn/interline/<int:pk>', cn_interlines_api.CNInterlineDetailApi.as_view(), name='CNInterlineDetailApiV3'),

    # Error Code
    path('error/codes', error_code_api.ErrorCodeApi.as_view(), name='ErrorCodeApiV3'),
    path('error/codes/<int:pk>', error_code_api.ErrorCodeDetailApi.as_view(), name='ErrorCodeDetailApiV3'),
    path('error/upload', error_code_api.ErrorCodeUploadApi.as_view(), name='ErrorCodeUploadApiV3'),

    # Promo Codes
    path('promo_code/list', promo_code_api.PromoCodeApi.as_view(), name='PromoCodeApiV3'),
    path('promo_code/list/<int:pk>', promo_code_api.PromoCodeDetailApi.as_view(), name='PromoCodeDetailApiV3'),
    path('promo_code/bulk', promo_code_api.PromoCodeBulkApi.as_view(), name='PromoCodeBulkApiV3'),
    path('promo_code/validate', promo_code_api.PromoCodeValidateApi.as_view(), name='PromoCodeValidateApiV3'),

    path('reports/accounts', account_report_api.AccountReportApi.as_view(), name='AccountReportApiV3'),
    path('reports/quote_history', quote_history_report_api.QuoteHistoryReportApi.as_view(), name='QuoteHistoryReportApiV3'),
    path('reports/quote_history/by_leg', quote_history_report_api.QuoteHistoryByLegReportApi.as_view(), name='QuoteHistoryByLegReportApiV3'),
    path('reports/shipment_overview', shipment_overview_report_api.ShipmentOverviewReportApi.as_view(), name='ShipmentOverviewReportApiV3'),
    path('reports/shipment_overview/admin', admin_shipment_overview_report_api.AdminShipmentOverviewReportApi.as_view(), name='AdminShipmentOverviewReportApiV3'),
    path('reports/tracking', report_api.TrackingReportApi.as_view(), name='TrackingReportApiV3'),

]

