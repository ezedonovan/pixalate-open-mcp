from typing import Literal

from pydantic import BaseModel, Field

from pixalate_open_mcp.models.dimensions import dimensions, metrics

DIMENSIONS = list(dimensions.get("properties").keys())
METRICS = list(metrics.get("properties").keys())


class QueryWhere(BaseModel):
    field: Literal[tuple(DIMENSIONS + METRICS)] = Field(description="Name of the field that can be filtered on.")
    operator: Literal["=", "!=", "CONTAINS"] = Field(description="Operator to use for the filter.")
    values: list[str | int | float] = Field(description="Possible values for the field.")
    join_operator: Literal["AND", "OR"] = Field(description="Join operator for the @values")

    def to_str(self) -> str:
        if self.operator == "CONTAINS":
            return (
                "("
                + f") {self.join_operator} (".join([
                    f"CONTAINS(LOWER({self.field}),LOWER('{value}'))" for value in self.values
                ])
                + ")"
            )
        else:
            return (
                "("
                + f") {self.join_operator} (".join([f"{self.field} {self.operator} '{value}'" for value in self.values])
                + ")"
            )


class QueryConstruct(BaseModel):
    selectDimension: list[Literal[tuple(DIMENSIONS)]] = Field(description="List of one or many dimensions to retrieve.")
    selectMetric: list[Literal[tuple(METRICS)]] = Field(description="List of one or many metrics to retrieve.")
    where: list[QueryWhere] = Field(default=None, description="List of one or many where filters.")
    dateFrom: str = Field(description="Start date in YYYY-MM-DD format")
    dateTo: str = Field(description="End date in YYYY-MM-DD format")
    sortBy: Literal[tuple(DIMENSIONS + METRICS)] = Field(
        default=None,
        description="List of one or many dimensions or metrics to sort by. If not specified, the default is to sort by the first dimension in the selectDimension list.",
    )
    sortByOrder: Literal["ASC", "DESC"] = Field(
        default="DESC", description="Sort order. If not specified, the default is to sort in descending order."
    )
    groupBy: list[Literal[tuple(DIMENSIONS + METRICS)]] = Field(
        default=None, description="List of one or many dimensions or metrics to group by."
    )

    def _construct_select(self):
        _select = []
        if self.selectDimension:
            _select.extend(self.selectDimension)
        if self.selectMetric:
            _select.extend(self.selectMetric)

        if self.sortBy:
            if self.sortBy not in _select:
                _select.append(self.sortBy)
        else:
            self.sortBy = _select[0]

        if self.groupBy:
            for field in self.groupBy:
                if field not in _select:
                    _select.append(field)

        return ",".join(_select)

    def _construct_date(self):
        return f"day>='{self.dateFrom}' AND day<='{self.dateTo}'"

    def _construct_where_filters(self):
        _where = self._construct_date()
        if self.where:
            if len(self.where) > 1:
                _where += " AND " + " AND ".join(["(" + where.to_str() + ")" for where in self.where])
            else:
                _where += " AND " + self.where[0].to_str()
        return "WHERE " + _where

    def _construct_group_by(self):
        if self.groupBy:
            return f"GROUP BY {','.join(self.groupBy)}"
        return ""

    def _construct_order_by(self):
        if self.sortBy:
            return f"ORDER BY {self.sortBy} {self.sortByOrder}"
        return ""

    def construct_query(self):
        _select = self._construct_select()
        _where = self._construct_where_filters()
        _group_by = self._construct_group_by()
        _order_by = self._construct_order_by()
        return f"{_select} {_where} {_group_by} {_order_by}"


class AnalyticsRequest(BaseModel):
    reportId: str = Field(
        default="default",
        description="The report's unique identifier. To request the default analytics report, use the term default as the report identifier.",
    )
    timeZone: int = Field(
        default=0,
        description="The time zone in which to sync the report data. The timezone is the number of minutes from GMT. Default is 0.",
    )
    start: int = Field(default=0, description="The offset start item.")
    limit: int = Field(default=20, description="The total number of items to return. Default is 20.")
    q: QueryConstruct = Field(
        default="",
        description="""A URL encoded query to run to retrieve data. It uses a simplified SQL SELECT syntax as follows:

[ column [ ,column... ] ] [ WHERE expression ] [ GROUP BY column [ ,column... ] ] [ ORDER BY column [ DESC ] ]

Note: All characters and their values are case sensitive.

column	dimension or metric
dimension	One of the set of dimension identifiers available for the specified report. See Dimensions schema below.
metric	One of the set of metric identifiers available for the specified report. See Metrics schema below.
expression	One of the following: dimension operator literal, or metric comparator literal, or (expression), or expression AND expression, or expression OR expression, or CONTAINS (dimension, or literal)
operator	=, or !=
comparator	=, or >, or <
literal	number, or string, or date
number	An integer or decimal number.
string	A text string surrounded by single quotes.
date	A date as yyyy-mm-dd format surrounded by single quotes.
Example : impressions,nonGivtViews,nonGivtViewsRate,nonGivtViewability,viewability,givtSivtRate,sivtRate,givtRate WHERE day>='2023-01-16' AND day<='2023-01-16' ORDER BY impressions DESC""",
    )
    exportUri: bool = Field(
        default=False,
        description="Setting this flag to true indicates that the API returns a URI to the CSV data as an Internet resource rather than the data itself. While the resulting resource is public, the URI contains a randomly generated identifier that ensures the data is relatively secure unless the URI itself is made public by the user.",
    )
    isAsync: bool = Field(
        default=True,
        description="If set to true, a CSV URI response is returned immediately. However, this will return a 404 Not Found HTTP status code until the service completes processing the report. Note that this parameter is only recognized when the exportUri parameter is also supplied as true. Note also that the limit parameter is ignored when this parameter is set to true.",
    )
    isLargeResultSet: bool = Field(
        default=False,
        description="""If set to true, then processing is handled identically as if the isAsync parameter is set to true. However, the returned CSV file contains a single column with each row being a URL to a CSV file that contains part of the data. Large results that set ORDER BY may cause an 400 Bad Request HTTP status code. To resolve, try removing the ORDER BY clause. Note that this parameter is only recognized when the exportUri parameter is also supplied as true. Note also that the limit parameter is ignored when this parameter is set to true.""",
    )

    def to_params(self):
        return {
            "timeZone": self.timeZone,
            "start": self.start,
            "limit": self.limit,
            "q": self.q.construct_query(),
            "exportUri": self.exportUri,
            "isAsync": self.isAsync,
            "isLargeResultSet": self.isLargeResultSet,
        }


class AnalyticsResponse(BaseModel):
    numFound: int = Field(description="The total number of documents matching the query.")
    docs: list[dict] = Field(description="The documents matching the query.")
