"""Restricted, deterministic regulatory-condition validation and evaluation."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator


class ConditionDefinitionError(ValueError):
    """Raised when a governed condition definition is invalid."""


class FactValueError(ValueError):
    """Raised when a supplied fact value violates its governed definition."""


class TruthValue(StrEnum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class FactDataType(StrEnum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    ENUM = "enum"


class ConditionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FactDefinition(ConditionModel):
    code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
    data_type: FactDataType
    allowed_values: tuple[str, ...] | None = None
    unit: str | None = None

    @model_validator(mode="after")
    def validate_type_metadata(self) -> FactDefinition:
        if self.data_type is FactDataType.ENUM:
            if not self.allowed_values or len(set(self.allowed_values)) != len(self.allowed_values):
                raise ValueError("enum facts require unique allowed values")
        elif self.allowed_values is not None:
            raise ValueError("only enum facts may define allowed values")
        return self


type Scalar = bool | int | Decimal | str


class EqualityPredicate(ConditionModel):
    op: Literal["eq"]
    fact: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
    value: Scalar


class AllCondition(ConditionModel):
    op: Literal["and"]
    args: Annotated[tuple[ConditionExpression, ...], Field(min_length=2)]


class AnyCondition(ConditionModel):
    op: Literal["or"]
    args: Annotated[tuple[ConditionExpression, ...], Field(min_length=2)]


class NotCondition(ConditionModel):
    op: Literal["not"]
    arg: ConditionExpression


type ConditionExpression = Annotated[
    EqualityPredicate | AllCondition | AnyCondition | NotCondition,
    Field(discriminator="op"),
]

_EXPRESSION_ADAPTER: TypeAdapter[ConditionExpression] = TypeAdapter(ConditionExpression)


def parse_condition(value: object) -> ConditionExpression:
    """Parse a strict condition tree; arbitrary fields and operators are rejected."""

    # JSON arrays arrive as Python lists; Pydantic normalizes them to immutable
    # tuples while the explicit fact-type validator below remains authoritative.
    return _EXPRESSION_ADAPTER.validate_python(value)


def condition_sha256(expression: ConditionExpression) -> str:
    """Return the stable canonical JSON hash used by packages and database rows."""

    payload = _EXPRESSION_ADAPTER.dump_python(expression, mode="json")
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def referenced_fact_codes(expression: ConditionExpression) -> frozenset[str]:
    """Return every governed fact code referenced by a condition tree."""

    if isinstance(expression, EqualityPredicate):
        return frozenset((expression.fact,))
    if isinstance(expression, NotCondition):
        return referenced_fact_codes(expression.arg)
    return frozenset().union(*(referenced_fact_codes(item) for item in expression.args))


def _validate_scalar(value: object, fact: FactDefinition) -> Scalar:
    if fact.data_type is FactDataType.BOOLEAN:
        if type(value) is not bool:
            raise FactValueError(f"{fact.code} requires a boolean")
        return value
    if fact.data_type is FactDataType.INTEGER:
        if type(value) is not int:
            raise FactValueError(f"{fact.code} requires an integer")
        return value
    if fact.data_type is FactDataType.DECIMAL:
        if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
            raise FactValueError(f"{fact.code} requires a decimal-compatible number")
        return Decimal(value)
    if type(value) is not str or value not in (fact.allowed_values or ()):
        raise FactValueError(f"{fact.code} requires an approved enum value")
    return value


def validate_condition_definition(
    expression: ConditionExpression,
    definitions: dict[str, FactDefinition],
) -> None:
    """Prove operators and literal values match the governed fact vocabulary."""

    for code in referenced_fact_codes(expression):
        if code not in definitions:
            raise ConditionDefinitionError(f"unknown governed fact code: {code}")

    def visit(node: ConditionExpression) -> None:
        if isinstance(node, EqualityPredicate):
            fact = definitions[node.fact]
            try:
                _validate_scalar(node.value, fact)
            except FactValueError as exc:
                raise ConditionDefinitionError(str(exc)) from exc
            return
        if isinstance(node, NotCondition):
            visit(node.arg)
            return
        for child in node.args:
            visit(child)

    visit(expression)


def truth_not(value: TruthValue) -> TruthValue:
    return {
        TruthValue.TRUE: TruthValue.FALSE,
        TruthValue.FALSE: TruthValue.TRUE,
        TruthValue.UNKNOWN: TruthValue.UNKNOWN,
    }[value]


def truth_and(values: tuple[TruthValue, ...]) -> TruthValue:
    if TruthValue.FALSE in values:
        return TruthValue.FALSE
    if TruthValue.UNKNOWN in values:
        return TruthValue.UNKNOWN
    return TruthValue.TRUE


def truth_or(values: tuple[TruthValue, ...]) -> TruthValue:
    if TruthValue.TRUE in values:
        return TruthValue.TRUE
    if TruthValue.UNKNOWN in values:
        return TruthValue.UNKNOWN
    return TruthValue.FALSE


def evaluate_condition(
    expression: ConditionExpression,
    definitions: dict[str, FactDefinition],
    fact_values: dict[str, object],
) -> TruthValue:
    """Evaluate verified facts without ever treating an absent fact as false."""

    validate_condition_definition(expression, definitions)
    unknown_inputs = set(fact_values) - set(definitions)
    if unknown_inputs:
        raise FactValueError(f"unknown input fact code: {sorted(unknown_inputs)[0]}")

    validated_values = {
        code: _validate_scalar(value, definitions[code]) for code, value in fact_values.items()
    }

    def visit(node: ConditionExpression) -> TruthValue:
        if isinstance(node, EqualityPredicate):
            if node.fact not in validated_values:
                return TruthValue.UNKNOWN
            actual = validated_values[node.fact]
            expected = _validate_scalar(node.value, definitions[node.fact])
            return TruthValue.TRUE if actual == expected else TruthValue.FALSE
        if isinstance(node, NotCondition):
            return truth_not(visit(node.arg))
        values = tuple(visit(child) for child in node.args)
        if isinstance(node, AllCondition):
            return truth_and(values)
        return truth_or(values)

    return visit(expression)


__all__ = [
    "ConditionDefinitionError",
    "ConditionExpression",
    "FactDataType",
    "FactDefinition",
    "FactValueError",
    "TruthValue",
    "condition_sha256",
    "evaluate_condition",
    "parse_condition",
    "referenced_fact_codes",
    "truth_and",
    "truth_not",
    "truth_or",
    "validate_condition_definition",
]
