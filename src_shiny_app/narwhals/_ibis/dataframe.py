from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from narwhals.dependencies import get_ibis

if TYPE_CHECKING:
    from types import ModuleType

    import pandas as pd
    import pyarrow as pa
    from typing_extensions import Self

    from narwhals._ibis.series import IbisInterchangeSeries
    from narwhals.dtypes import DType
    from narwhals.typing import DTypes


def map_ibis_dtype_to_narwhals_dtype(ibis_dtype: Any, dtypes: DTypes) -> DType:
    if ibis_dtype.is_int64():
        return dtypes.Int64()
    if ibis_dtype.is_int32():
        return dtypes.Int32()
    if ibis_dtype.is_int16():
        return dtypes.Int16()
    if ibis_dtype.is_int8():
        return dtypes.Int8()
    if ibis_dtype.is_uint64():
        return dtypes.UInt64()
    if ibis_dtype.is_uint32():
        return dtypes.UInt32()
    if ibis_dtype.is_uint16():
        return dtypes.UInt16()
    if ibis_dtype.is_uint8():
        return dtypes.UInt8()
    if ibis_dtype.is_boolean():
        return dtypes.Boolean()
    if ibis_dtype.is_float64():
        return dtypes.Float64()
    if ibis_dtype.is_float32():
        return dtypes.Float32()
    if ibis_dtype.is_string():
        return dtypes.String()
    if ibis_dtype.is_date():
        return dtypes.Date()
    if ibis_dtype.is_timestamp():
        return dtypes.Datetime()
    if ibis_dtype.is_array():
        return dtypes.List(
            map_ibis_dtype_to_narwhals_dtype(ibis_dtype.value_type, dtypes)
        )
    if ibis_dtype.is_struct():
        return dtypes.Struct(
            [
                dtypes.Field(
                    ibis_dtype_name,
                    map_ibis_dtype_to_narwhals_dtype(ibis_dtype_field, dtypes),
                )
                for ibis_dtype_name, ibis_dtype_field in ibis_dtype.items()
            ]
        )
    return dtypes.Unknown()  # pragma: no cover


class IbisInterchangeFrame:
    def __init__(self, df: Any, dtypes: DTypes) -> None:
        self._native_frame = df
        self._dtypes = dtypes

    def __narwhals_dataframe__(self) -> Any:
        return self

    def __native_namespace__(self: Self) -> ModuleType:
        return get_ibis()  # type: ignore[no-any-return]

    def __getitem__(self, item: str) -> IbisInterchangeSeries:
        from narwhals._ibis.series import IbisInterchangeSeries

        return IbisInterchangeSeries(self._native_frame[item], dtypes=self._dtypes)

    def to_pandas(self: Self) -> pd.DataFrame:
        return self._native_frame.to_pandas()

    def to_arrow(self: Self) -> pa.Table:
        return self._native_frame.to_pyarrow()

    def select(
        self: Self,
        *exprs: Any,
        **named_exprs: Any,
    ) -> Self:
        if named_exprs or not all(isinstance(x, str) for x in exprs):  # pragma: no cover
            msg = (
                "`select`-ing not by name is not supported for Ibis backend.\n\n"
                "If you would like to see this kind of object better supported in "
                "Narwhals, please open a feature request "
                "at https://github.com/narwhals-dev/narwhals/issues."
            )
            raise NotImplementedError(msg)

        import ibis.selectors as s

        return self._from_native_frame(self._native_frame.select(s.cols(*exprs)))

    def __getattr__(self, attr: str) -> Any:
        if attr == "schema":
            return {
                column_name: map_ibis_dtype_to_narwhals_dtype(ibis_dtype, self._dtypes)
                for column_name, ibis_dtype in self._native_frame.schema().items()
            }
        elif attr == "columns":
            return self._native_frame.columns
        msg = (
            f"Attribute {attr} is not supported for metadata-only dataframes.\n\n"
            "If you would like to see this kind of object better supported in "
            "Narwhals, please open a feature request "
            "at https://github.com/narwhals-dev/narwhals/issues."
        )
        raise NotImplementedError(msg)

    def _from_native_frame(self: Self, df: Any) -> Self:
        return self.__class__(df, dtypes=self._dtypes)