"""Tests for Pixalate MCP model classes."""

import pytest
from pydantic import ValidationError

from pixalate_open_mcp.models.analytics import AnalyticsRequest, QueryConstruct, QueryWhere
from pixalate_open_mcp.models.enrichment import EnrichmentCTVRequest, EnrichmentDomainRequest, EnrichmentMobileRequest
from pixalate_open_mcp.models.fraud import FraudRequest

# ---------------------------------------------------------------------------
# QueryWhere tests
# ---------------------------------------------------------------------------


def test_query_where_equals_operator():
    qw = QueryWhere(field="adDomain", operator="=", values=["yahoo.com"], join_operator="OR")
    assert qw.to_str() == "(adDomain = 'yahoo.com')"


def test_query_where_not_equals_operator():
    qw = QueryWhere(field="adDomain", operator="!=", values=["yahoo.com"], join_operator="OR")
    assert qw.to_str() == "(adDomain != 'yahoo.com')"


def test_query_where_contains_operator():
    qw = QueryWhere(field="adDomain", operator="CONTAINS", values=["yahoo.com"], join_operator="OR")
    assert qw.to_str() == "(CONTAINS(LOWER(adDomain),LOWER('yahoo.com')))"


def test_query_where_multiple_values_joined():
    qw = QueryWhere(field="adDomain", operator="=", values=["a", "b"], join_operator="OR")
    result = qw.to_str()
    assert ") OR (" in result
    assert "adDomain = 'a'" in result
    assert "adDomain = 'b'" in result


def test_query_where_multiple_values_and_join():
    qw = QueryWhere(field="adDomain", operator="=", values=["a", "b"], join_operator="AND")
    result = qw.to_str()
    assert ") AND (" in result


def test_query_where_contains_multiple_values():
    qw = QueryWhere(field="adDomain", operator="CONTAINS", values=["foo", "bar"], join_operator="OR")
    result = qw.to_str()
    assert "CONTAINS(LOWER(adDomain),LOWER('foo'))" in result
    assert "CONTAINS(LOWER(adDomain),LOWER('bar'))" in result
    assert ") OR (" in result


# ---------------------------------------------------------------------------
# QueryConstruct tests
# ---------------------------------------------------------------------------


def _make_query(**kwargs):
    defaults = {
        "selectDimension": ["day"],
        "selectMetric": ["impressions"],
        "dateFrom": "2024-01-01",
        "dateTo": "2024-01-31",
    }
    defaults.update(kwargs)
    return QueryConstruct(**defaults)


def test_construct_query_basic():
    qc = _make_query()
    result = qc.construct_query()
    assert "day" in result
    assert "impressions" in result
    assert "WHERE" in result
    assert "day>='2024-01-01'" in result
    assert "day<='2024-01-31'" in result
    assert "ORDER BY" in result


def test_construct_query_with_where_filters():
    where_filter = QueryWhere(field="adDomain", operator="=", values=["yahoo.com"], join_operator="OR")
    qc = _make_query(where=[where_filter])
    result = qc.construct_query()
    assert "adDomain = 'yahoo.com'" in result
    # Date clause must appear before the extra filter
    date_pos = result.index("day>='2024-01-01'")
    filter_pos = result.index("adDomain")
    assert date_pos < filter_pos


def test_construct_query_with_group_by():
    qc = _make_query(groupBy=["day"])
    result = qc.construct_query()
    assert "GROUP BY day" in result


def test_construct_query_with_sort_by():
    qc = _make_query(sortBy="impressions", sortByOrder="DESC")
    result = qc.construct_query()
    assert "ORDER BY impressions DESC" in result


def test_construct_query_default_sort_by():
    # When sortBy is not provided it defaults to the first selected column
    qc = _make_query()
    result = qc.construct_query()
    # First column is "day" (selectDimension)
    assert "ORDER BY day" in result


def test_construct_select_adds_sort_by_if_missing():
    # sortBy exists but is not in selected columns → should be appended
    qc = _make_query(selectDimension=["day"], selectMetric=["impressions"], sortBy="impressions")
    _select = qc._construct_select()
    # "impressions" is already in metrics, so it should not be duplicated
    assert _select.count("impressions") == 1


def test_construct_date():
    qc = _make_query(dateFrom="2023-06-01", dateTo="2023-06-30")
    assert qc._construct_date() == "day>='2023-06-01' AND day<='2023-06-30'"


def test_construct_where_no_filters():
    qc = _make_query()
    result = qc._construct_where_filters()
    assert result.startswith("WHERE ")
    assert "adDomain" not in result


def test_construct_where_multiple_filters():
    f1 = QueryWhere(field="adDomain", operator="=", values=["a.com"], join_operator="OR")
    f2 = QueryWhere(field="adDomain", operator="!=", values=["b.com"], join_operator="OR")
    qc = _make_query(where=[f1, f2])
    result = qc._construct_where_filters()
    assert "a.com" in result
    assert "b.com" in result


def test_construct_group_by_empty():
    qc = _make_query()
    assert qc._construct_group_by() == ""


def test_construct_order_by_asc():
    qc = _make_query(sortBy="impressions", sortByOrder="ASC")
    # _construct_select must be called first so sortBy is set
    qc._construct_select()
    assert qc._construct_order_by() == "ORDER BY impressions ASC"


# ---------------------------------------------------------------------------
# AnalyticsRequest tests
# ---------------------------------------------------------------------------


def _make_analytics_request(**kwargs):
    q = _make_query()
    defaults = {"q": q}
    defaults.update(kwargs)
    return AnalyticsRequest(**defaults)


def test_analytics_request_to_params():
    req = _make_analytics_request()
    params = req.to_params()
    assert "timeZone" in params
    assert "start" in params
    assert "limit" in params
    assert "q" in params
    assert "exportUri" in params
    assert "isAsync" in params
    assert "isLargeResultSet" in params


def test_analytics_request_defaults():
    req = _make_analytics_request()
    assert req.start == 0
    assert req.limit == 20
    assert req.timeZone == 0
    assert req.exportUri is False
    assert req.isAsync is True
    assert req.isLargeResultSet is False


def test_analytics_request_to_params_q_is_string():
    req = _make_analytics_request()
    params = req.to_params()
    assert isinstance(params["q"], str)
    assert len(params["q"]) > 0


# ---------------------------------------------------------------------------
# FraudRequest tests
# ---------------------------------------------------------------------------


def test_fraud_request_to_params_ip_only():
    req = FraudRequest(ip="1.2.3.4")
    assert req.to_params() == {"ip": "1.2.3.4"}


def test_fraud_request_to_params_device_id_only():
    req = FraudRequest(deviceId="FF67345D-BF11-7823-1111-FFED421776FC")
    assert req.to_params() == {"deviceId": "FF67345D-BF11-7823-1111-FFED421776FC"}


def test_fraud_request_to_params_user_agent_only():
    req = FraudRequest(userAgent="Mozilla/5.0")
    assert req.to_params() == {"userAgent": "Mozilla/5.0"}


def test_fraud_request_to_params_all_fields():
    req = FraudRequest(ip="1.2.3.4", deviceId="some-device", userAgent="Mozilla/5.0")
    params = req.to_params()
    assert params == {"ip": "1.2.3.4", "deviceId": "some-device", "userAgent": "Mozilla/5.0"}


def test_fraud_request_requires_at_least_one_field():
    with pytest.raises((ValueError, ValidationError)):
        FraudRequest()


def test_fraud_request_excludes_none_fields():
    req = FraudRequest(ip="1.2.3.4")
    params = req.to_params()
    assert "deviceId" not in params
    assert "userAgent" not in params


# ---------------------------------------------------------------------------
# EnrichmentMobileRequest tests
# ---------------------------------------------------------------------------


def test_mobile_request_to_params_defaults():
    req = EnrichmentMobileRequest(appIds=["com.example.app"])
    params = req.to_params()
    assert params["device"] == "GLOBAL"
    assert params["region"] == "GLOBAL"
    assert "widget" in params
    assert isinstance(params["widget"], list)
    assert len(params["widget"]) > 0


def test_mobile_request_to_params_with_filters():
    req = EnrichmentMobileRequest(appIds=["com.example.app"], device="tablet", region="EMEA")
    params = req.to_params()
    assert params["device"] == "tablet"
    assert params["region"] == "EMEA"


def test_mobile_request_to_params_custom_widget():
    req = EnrichmentMobileRequest(appIds=["com.example.app"], widget=["appOverview", "riskOverview"])
    params = req.to_params()
    assert params["widget"] == ["appOverview", "riskOverview"]


def test_mobile_request_to_params_keys():
    req = EnrichmentMobileRequest(appIds=["com.example.app"])
    params = req.to_params()
    assert set(params.keys()) == {"device", "region", "widget"}


# ---------------------------------------------------------------------------
# EnrichmentCTVRequest tests
# ---------------------------------------------------------------------------


def test_ctv_request_to_params():
    req = EnrichmentCTVRequest(appIds=["some-ctv-app"], device="roku")
    params = req.to_params()
    assert params["device"] == "roku"
    assert params["region"] == "GLOBAL"
    assert params["includeSpoofing"] is True


def test_ctv_request_to_params_custom_values():
    req = EnrichmentCTVRequest(
        appIds=["some-ctv-app"],
        device="firetv",
        region="NA",
        includeSpoofing=False,
    )
    params = req.to_params()
    assert params["device"] == "firetv"
    assert params["region"] == "NA"
    assert params["includeSpoofing"] is False


def test_ctv_request_to_params_keys():
    req = EnrichmentCTVRequest(appIds=["app"], device="tvos")
    params = req.to_params()
    assert set(params.keys()) == {"device", "region", "includeSpoofing"}


# ---------------------------------------------------------------------------
# EnrichmentDomainRequest tests
# ---------------------------------------------------------------------------


def test_domain_request_to_params():
    req = EnrichmentDomainRequest(adDomain=["example.com"])
    params = req.to_params()
    assert params["device"] == "GLOBAL"
    assert params["region"] == "GLOBAL"


def test_domain_request_to_params_custom_values():
    req = EnrichmentDomainRequest(adDomain=["example.com"], device="desktop", region="US")
    params = req.to_params()
    assert params["device"] == "desktop"
    assert params["region"] == "US"


def test_domain_request_to_params_keys():
    req = EnrichmentDomainRequest(adDomain=["example.com"])
    params = req.to_params()
    assert set(params.keys()) == {"device", "region"}
