from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Generic
from typing import Iterable
from typing import Literal
from typing import Mapping
from typing import Sequence
from typing import TypeVar

from narwhals.dependencies import is_numpy_array
from narwhals.utils import flatten

if TYPE_CHECKING:
    from typing_extensions import Self

    from narwhals.dtypes import DType
    from narwhals.typing import IntoExpr


def extract_compliant(expr: Expr, other: Any) -> Any:
    from narwhals.series import Series

    if isinstance(other, Expr):
        return other._call(expr)
    if isinstance(other, Series):
        return other._compliant_series
    return other


class Expr:
    def __init__(self, call: Callable[[Any], Any]) -> None:
        # callable from namespace to expr
        self._call = call

    def _taxicab_norm(self) -> Self:
        # This is just used to test out the stable api feature in a realistic-ish way.
        # It's not intended to be used.
        return self.__class__(lambda plx: self._call(plx).abs().sum())

    # --- convert ---
    def alias(self, name: str) -> Self:
        """
        Rename the expression.

        Arguments:
            name: The new name.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 2], "b": [4, 5]})
            >>> df_pl = pl.DataFrame({"a": [1, 2], "b": [4, 5]})
            >>> df_pa = pa.table({"a": [1, 2], "b": [4, 5]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select((nw.col("b") + 10).alias("c"))

            We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                c
            0  14
            1  15
            >>> func(df_pl)
            shape: (2, 1)
            ┌─────┐
            │ c   │
            │ --- │
            │ i64 │
            ╞═════╡
            │ 14  │
            │ 15  │
            └─────┘
            >>> func(df_pa)
            pyarrow.Table
            c: int64
            ----
            c: [[14,15]]

        """
        return self.__class__(lambda plx: self._call(plx).alias(name))

    def pipe(self, function: Callable[[Any], Self], *args: Any, **kwargs: Any) -> Self:
        """
        Pipe function call.

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> data = {"a": [1, 2, 3, 4]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Lets define a library-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").pipe(lambda x: x + 1))

            We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a
            0  2
            1  3
            2  4
            3  5
            >>> func(df_pl)
            shape: (4, 1)
            ┌─────┐
            │ a   │
            │ --- │
            │ i64 │
            ╞═════╡
            │ 2   │
            │ 3   │
            │ 4   │
            │ 5   │
            └─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            ----
            a: [[2,3,4,5]]
        """
        return function(self, *args, **kwargs)

    def cast(self: Self, dtype: DType | type[DType]) -> Self:
        """
        Redefine an object's data type.

        Arguments:
            dtype: Data type that the object will be cast into.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> from datetime import date
            >>> df_pd = pd.DataFrame({"foo": [1, 2, 3], "bar": [6.0, 7.0, 8.0]})
            >>> df_pl = pl.DataFrame({"foo": [1, 2, 3], "bar": [6.0, 7.0, 8.0]})
            >>> df_pa = pa.table({"foo": [1, 2, 3], "bar": [6.0, 7.0, 8.0]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(
            ...         nw.col("foo").cast(nw.Float32), nw.col("bar").cast(nw.UInt8)
            ...     )

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               foo  bar
            0  1.0    6
            1  2.0    7
            2  3.0    8
            >>> func(df_pl)
            shape: (3, 2)
            ┌─────┬─────┐
            │ foo ┆ bar │
            │ --- ┆ --- │
            │ f32 ┆ u8  │
            ╞═════╪═════╡
            │ 1.0 ┆ 6   │
            │ 2.0 ┆ 7   │
            │ 3.0 ┆ 8   │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            foo: float
            bar: uint8
            ----
            foo: [[1,2,3]]
            bar: [[6,7,8]]
        """
        return self.__class__(
            lambda plx: self._call(plx).cast(dtype),
        )

    # --- binary ---
    def __eq__(self, other: object) -> Self:  # type: ignore[override]
        return self.__class__(
            lambda plx: self._call(plx).__eq__(extract_compliant(plx, other))
        )

    def __ne__(self, other: object) -> Self:  # type: ignore[override]
        return self.__class__(
            lambda plx: self._call(plx).__ne__(extract_compliant(plx, other))
        )

    def __and__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__and__(extract_compliant(plx, other))
        )

    def __rand__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__rand__(extract_compliant(plx, other))
        )

    def __or__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__or__(extract_compliant(plx, other))
        )

    def __ror__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__ror__(extract_compliant(plx, other))
        )

    def __add__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__add__(extract_compliant(plx, other))
        )

    def __radd__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__radd__(extract_compliant(plx, other))
        )

    def __sub__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__sub__(extract_compliant(plx, other))
        )

    def __rsub__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__rsub__(extract_compliant(plx, other))
        )

    def __truediv__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__truediv__(extract_compliant(plx, other))
        )

    def __rtruediv__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__rtruediv__(extract_compliant(plx, other))
        )

    def __mul__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__mul__(extract_compliant(plx, other))
        )

    def __rmul__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__rmul__(extract_compliant(plx, other))
        )

    def __le__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__le__(extract_compliant(plx, other))
        )

    def __lt__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__lt__(extract_compliant(plx, other))
        )

    def __gt__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__gt__(extract_compliant(plx, other))
        )

    def __ge__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__ge__(extract_compliant(plx, other))
        )

    def __pow__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__pow__(extract_compliant(plx, other))
        )

    def __rpow__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__rpow__(extract_compliant(plx, other))
        )

    def __floordiv__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__floordiv__(extract_compliant(plx, other))
        )

    def __rfloordiv__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__rfloordiv__(extract_compliant(plx, other))
        )

    def __mod__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__mod__(extract_compliant(plx, other))
        )

    def __rmod__(self, other: Any) -> Self:
        return self.__class__(
            lambda plx: self._call(plx).__rmod__(extract_compliant(plx, other))
        )

    # --- unary ---
    def __invert__(self) -> Self:
        return self.__class__(lambda plx: self._call(plx).__invert__())

    def any(self) -> Self:
        """
        Return whether any of the values in the column are `True`

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [True, False], "b": [True, True]})
            >>> df_pl = pl.DataFrame({"a": [True, False], "b": [True, True]})
            >>> df_pa = pa.table({"a": [True, False], "b": [True, True]})

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").any())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                  a     b
            0  True  True
            >>> func(df_pl)
            shape: (1, 2)
            ┌──────┬──────┐
            │ a    ┆ b    │
            │ ---  ┆ ---  │
            │ bool ┆ bool │
            ╞══════╪══════╡
            │ true ┆ true │
            └──────┴──────┘
            >>> func(df_pa)
            pyarrow.Table
            a: bool
            b: bool
            ----
            a: [[true]]
            b: [[true]]
        """
        return self.__class__(lambda plx: self._call(plx).any())

    def all(self) -> Self:
        """
        Return whether all values in the column are `True`.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [True, False], "b": [True, True]})
            >>> df_pl = pl.DataFrame({"a": [True, False], "b": [True, True]})
            >>> df_pa = pa.table({"a": [True, False], "b": [True, True]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").all())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                   a     b
            0  False  True
            >>> func(df_pl)
            shape: (1, 2)
            ┌───────┬──────┐
            │ a     ┆ b    │
            │ ---   ┆ ---  │
            │ bool  ┆ bool │
            ╞═══════╪══════╡
            │ false ┆ true │
            └───────┴──────┘
            >>> func(df_pa)
            pyarrow.Table
            a: bool
            b: bool
            ----
            a: [[false]]
            b: [[true]]
        """
        return self.__class__(lambda plx: self._call(plx).all())

    def mean(self) -> Self:
        """
        Get mean value.

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [-1, 0, 1], "b": [2, 4, 6]})
            >>> df_pl = pl.DataFrame({"a": [-1, 0, 1], "b": [2, 4, 6]})
            >>> df_pa = pa.table({"a": [-1, 0, 1], "b": [2, 4, 6]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").mean())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                 a    b
            0  0.0  4.0
            >>> func(df_pl)
            shape: (1, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ f64 ┆ f64 │
            ╞═════╪═════╡
            │ 0.0 ┆ 4.0 │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: double
            b: double
            ----
            a: [[0]]
            b: [[4]]
        """
        return self.__class__(lambda plx: self._call(plx).mean())

    def median(self) -> Self:
        """
        Get median value.

        Notes:
            Results might slightly differ across backends due to differences in the underlying algorithms used to compute the median.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 8, 3], "b": [4, 5, 2]})
            >>> df_pl = pl.DataFrame({"a": [1, 8, 3], "b": [4, 5, 2]})
            >>> df_pa = pa.table({"a": [1, 8, 3], "b": [4, 5, 2]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").median())

            We can then pass any supported library such as pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                 a    b
            0  3.0  4.0
            >>> func(df_pl)
            shape: (1, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ f64 ┆ f64 │
            ╞═════╪═════╡
            │ 3.0 ┆ 4.0 │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: double
            b: double
            ----
            a: [[3]]
            b: [[4]]
        """
        return self.__class__(lambda plx: self._call(plx).median())

    def std(self, *, ddof: int = 1) -> Self:
        """
        Get standard deviation.

        Arguments:
            ddof: “Delta Degrees of Freedom”: the divisor used in the calculation is N - ddof,
                     where N represents the number of elements. By default ddof is 1.

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [20, 25, 60], "b": [1.5, 1, -1.4]})
            >>> df_pl = pl.DataFrame({"a": [20, 25, 60], "b": [1.5, 1, -1.4]})
            >>> df_pa = pa.table({"a": [20, 25, 60], "b": [1.5, 1, -1.4]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").std(ddof=0))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                      a         b
            0  17.79513  1.265789
            >>> func(df_pl)
            shape: (1, 2)
            ┌──────────┬──────────┐
            │ a        ┆ b        │
            │ ---      ┆ ---      │
            │ f64      ┆ f64      │
            ╞══════════╪══════════╡
            │ 17.79513 ┆ 1.265789 │
            └──────────┴──────────┘
            >>> func(df_pa)
            pyarrow.Table
            a: double
            b: double
            ----
            a: [[17.795130420052185]]
            b: [[1.2657891697365016]]

        """
        return self.__class__(lambda plx: self._call(plx).std(ddof=ddof))

    def map_batches(
        self,
        function: Callable[[Any], Self],
        return_dtype: DType | None = None,
    ) -> Self:
        """
        Apply a custom python function to a whole Series or sequence of Series.

        The output of this custom function is presumed to be either a Series,
        or a NumPy array (in which case it will be automatically converted into
        a Series).

        Arguments:
            return_dtype: Dtype of the output Series.
                          If not set, the dtype will be inferred based on the first non-null value
                          that is returned by the function.

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> data = {"a": [1, 2, 3], "b": [4, 5, 6]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(
            ...         nw.col("a", "b").map_batches(
            ...             lambda s: s.to_numpy() + 1, return_dtype=nw.Float64
            ...         )
            ...     )

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                 a    b
            0  2.0  5.0
            1  3.0  6.0
            2  4.0  7.0
            >>> func(df_pl)
            shape: (3, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ f64 ┆ f64 │
            ╞═════╪═════╡
            │ 2.0 ┆ 5.0 │
            │ 3.0 ┆ 6.0 │
            │ 4.0 ┆ 7.0 │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: double
            b: double
            ----
            a: [[2,3,4]]
            b: [[5,6,7]]
        """
        return self.__class__(
            lambda plx: self._call(plx).map_batches(
                function=function, return_dtype=return_dtype
            )
        )

    def sum(self) -> Expr:
        """
        Return the sum value.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [5, 10], "b": [50, 100]})
            >>> df_pl = pl.DataFrame({"a": [5, 10], "b": [50, 100]})
            >>> df_pa = pa.table({"a": [5, 10], "b": [50, 100]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").sum())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                a    b
            0  15  150
            >>> func(df_pl)
            shape: (1, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ i64 ┆ i64 │
            ╞═════╪═════╡
            │ 15  ┆ 150 │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[15]]
            b: [[150]]
        """
        return self.__class__(lambda plx: self._call(plx).sum())

    def min(self) -> Self:
        """
        Returns the minimum value(s) from a column(s).

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 2], "b": [4, 3]})
            >>> df_pl = pl.DataFrame({"a": [1, 2], "b": [4, 3]})
            >>> df_pa = pa.table({"a": [1, 2], "b": [4, 3]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.min("a", "b"))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a  b
            0  1  3
            >>> func(df_pl)
            shape: (1, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ i64 ┆ i64 │
            ╞═════╪═════╡
            │ 1   ┆ 3   │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[1]]
            b: [[3]]
        """
        return self.__class__(lambda plx: self._call(plx).min())

    def max(self) -> Self:
        """
        Returns the maximum value(s) from a column(s).

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [10, 20], "b": [50, 100]})
            >>> df_pl = pl.DataFrame({"a": [10, 20], "b": [50, 100]})
            >>> df_pa = pa.table({"a": [10, 20], "b": [50, 100]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.max("a", "b"))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                a    b
            0  20  100
            >>> func(df_pl)
            shape: (1, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ i64 ┆ i64 │
            ╞═════╪═════╡
            │ 20  ┆ 100 │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[20]]
            b: [[100]]
        """
        return self.__class__(lambda plx: self._call(plx).max())

    def count(self) -> Self:
        """
        Returns the number of non-null elements in the column.

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 2, 3], "b": [None, 4, 4]})
            >>> df_pl = pl.DataFrame({"a": [1, 2, 3], "b": [None, 4, 4]})
            >>> df_pa = pa.table({"a": [1, 2, 3], "b": [None, 4, 4]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.all().count())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a  b
            0  3  2
            >>> func(df_pl)
            shape: (1, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ u32 ┆ u32 │
            ╞═════╪═════╡
            │ 3   ┆ 2   │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[3]]
            b: [[2]]
        """
        return self.__class__(lambda plx: self._call(plx).count())

    def n_unique(self) -> Self:
        """
         Returns count of unique values

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [1, 1, 3, 3, 5]})
            >>> df_pl = pl.DataFrame({"a": [1, 2, 3, 4, 5], "b": [1, 1, 3, 3, 5]})
            >>> df_pa = pa.table({"a": [1, 2, 3, 4, 5], "b": [1, 1, 3, 3, 5]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").n_unique())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a  b
            0  5  3
            >>> func(df_pl)
            shape: (1, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ u32 ┆ u32 │
            ╞═════╪═════╡
            │ 5   ┆ 3   │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[5]]
            b: [[3]]
        """
        return self.__class__(lambda plx: self._call(plx).n_unique())

    def unique(self, *, maintain_order: bool = False) -> Self:
        """
        Return unique values of this expression.

        Arguments:
            maintain_order: Keep the same order as the original expression. This may be more
                expensive to compute. Settings this to `True` blocks the possibility
                to run on the streaming engine for Polars.

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 1, 3, 5, 5], "b": [2, 4, 4, 6, 6]})
            >>> df_pl = pl.DataFrame({"a": [1, 1, 3, 5, 5], "b": [2, 4, 4, 6, 6]})
            >>> df_pa = pa.table({"a": [1, 1, 3, 5, 5], "b": [2, 4, 4, 6, 6]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").unique(maintain_order=True))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a  b
            0  1  2
            1  3  4
            2  5  6
            >>> func(df_pl)
            shape: (3, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ i64 ┆ i64 │
            ╞═════╪═════╡
            │ 1   ┆ 2   │
            │ 3   ┆ 4   │
            │ 5   ┆ 6   │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[1,3,5]]
            b: [[2,4,6]]
        """
        return self.__class__(
            lambda plx: self._call(plx).unique(maintain_order=maintain_order)
        )

    def abs(self) -> Self:
        """
        Return absolute value of each element.

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> data = {"a": [1, -2], "b": [-3, 4]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").abs())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a  b
            0  1  3
            1  2  4
            >>> func(df_pl)
            shape: (2, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ i64 ┆ i64 │
            ╞═════╪═════╡
            │ 1   ┆ 3   │
            │ 2   ┆ 4   │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[1,2]]
            b: [[3,4]]
        """
        return self.__class__(lambda plx: self._call(plx).abs())

    def cum_sum(self) -> Self:
        """
        Return cumulative sum.

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 1, 3, 5, 5], "b": [2, 4, 4, 6, 6]})
            >>> df_pl = pl.DataFrame({"a": [1, 1, 3, 5, 5], "b": [2, 4, 4, 6, 6]})
            >>> df_pa = pa.table({"a": [1, 1, 3, 5, 5], "b": [2, 4, 4, 6, 6]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").cum_sum())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                a   b
            0   1   2
            1   2   6
            2   5  10
            3  10  16
            4  15  22
            >>> func(df_pl)
            shape: (5, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ i64 ┆ i64 │
            ╞═════╪═════╡
            │ 1   ┆ 2   │
            │ 2   ┆ 6   │
            │ 5   ┆ 10  │
            │ 10  ┆ 16  │
            │ 15  ┆ 22  │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[1,2,5,10,15]]
            b: [[2,6,10,16,22]]
        """
        return self.__class__(lambda plx: self._call(plx).cum_sum())

    def diff(self) -> Self:
        """
        Returns the difference between each element and the previous one.

        Notes:
            pandas may change the dtype here, for example when introducing missing
            values in an integer column. To ensure, that the dtype doesn't change,
            you may want to use `fill_null` and `cast`. For example, to calculate
            the diff and fill missing values with `0` in a Int64 column, you could
            do:

                nw.col("a").diff().fill_null(0).cast(nw.Int64)

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 1, 3, 5, 5]})
            >>> df_pl = pl.DataFrame({"a": [1, 1, 3, 5, 5]})
            >>> df_pa = pa.table({"a": [1, 1, 3, 5, 5]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(a_diff=nw.col("a").diff())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a_diff
            0     NaN
            1     0.0
            2     2.0
            3     2.0
            4     0.0
            >>> func(df_pl)
            shape: (5, 1)
            ┌────────┐
            │ a_diff │
            │ ---    │
            │ i64    │
            ╞════════╡
            │ null   │
            │ 0      │
            │ 2      │
            │ 2      │
            │ 0      │
            └────────┘
            >>> func(df_pa)
            pyarrow.Table
            a_diff: int64
            ----
            a_diff: [[null,0,2,2,0]]
        """
        return self.__class__(lambda plx: self._call(plx).diff())

    def shift(self, n: int) -> Self:
        """
        Shift values by `n` positions.

        Notes:
            pandas may change the dtype here, for example when introducing missing
            values in an integer column. To ensure, that the dtype doesn't change,
            you may want to use `fill_null` and `cast`. For example, to shift
            and fill missing values with `0` in a Int64 column, you could
            do:

                nw.col("a").shift(1).fill_null(0).cast(nw.Int64)

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 1, 3, 5, 5]})
            >>> df_pl = pl.DataFrame({"a": [1, 1, 3, 5, 5]})
            >>> df_pa = pa.table({"a": [1, 1, 3, 5, 5]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(a_shift=nw.col("a").shift(n=1))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a_shift
            0      NaN
            1      1.0
            2      1.0
            3      3.0
            4      5.0
            >>> func(df_pl)
            shape: (5, 1)
            ┌─────────┐
            │ a_shift │
            │ ---     │
            │ i64     │
            ╞═════════╡
            │ null    │
            │ 1       │
            │ 1       │
            │ 3       │
            │ 5       │
            └─────────┘
            >>> func(df_pa)
            pyarrow.Table
            a_shift: int64
            ----
            a_shift: [[null,1,1,3,5]]
        """
        return self.__class__(lambda plx: self._call(plx).shift(n))

    def replace_strict(
        self,
        old: Sequence[Any] | Mapping[Any, Any],
        new: Sequence[Any] | None = None,
        *,
        return_dtype: DType | type[DType] | None = None,
    ) -> Self:
        """
        Replace all values by different values.

        This function must replace all non-null input values (else it raises an error).

        Arguments:
            old: Sequence of values to replace. It also accepts a mapping of values to
                their replacement as syntactic sugar for
                `replace_all(old=list(mapping.keys()), new=list(mapping.values()))`.
            new: Sequence of values to replace by. Length must match the length of `old`.
            return_dtype: The data type of the resulting expression. If set to `None`
                (default), the data type is determined automatically based on the other
                inputs.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> df_pd = pd.DataFrame({"a": [3, 0, 1, 2]})
            >>> df_pl = pl.DataFrame({"a": [3, 0, 1, 2]})
            >>> df_pa = pa.table({"a": [3, 0, 1, 2]})

            Let's define dataframe-agnostic functions:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         b=nw.col("a").replace_strict(
            ...             [0, 1, 2, 3],
            ...             ["zero", "one", "two", "three"],
            ...             return_dtype=nw.String,
            ...         )
            ...     )

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a      b
            0  3  three
            1  0   zero
            2  1    one
            3  2    two
            >>> func(df_pl)
            shape: (4, 2)
            ┌─────┬───────┐
            │ a   ┆ b     │
            │ --- ┆ ---   │
            │ i64 ┆ str   │
            ╞═════╪═══════╡
            │ 3   ┆ three │
            │ 0   ┆ zero  │
            │ 1   ┆ one   │
            │ 2   ┆ two   │
            └─────┴───────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: string
            ----
            a: [[3,0,1,2]]
            b: [["three","zero","one","two"]]
        """
        if new is None:
            if not isinstance(old, Mapping):
                msg = "`new` argument is required if `old` argument is not a Mapping type"
                raise TypeError(msg)

            new = list(old.values())
            old = list(old.keys())

        return self.__class__(
            lambda plx: self._call(plx).replace_strict(
                old, new, return_dtype=return_dtype
            )
        )

    def sort(self, *, descending: bool = False, nulls_last: bool = False) -> Self:
        """
        Sort this column. Place null values first.

        Arguments:
            descending: Sort in descending order.
            nulls_last: Place null values last instead of first.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> df_pd = pd.DataFrame({"a": [5, None, 1, 2]})
            >>> df_pl = pl.DataFrame({"a": [5, None, 1, 2]})
            >>> df_pa = pa.table({"a": [5, None, 1, 2]})

            Let's define dataframe-agnostic functions:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").sort())

            >>> def func_descend(df):
            ...     df = nw.from_native(df)
            ...     df = df.select(nw.col("a").sort(descending=True))
            ...     return nw.to_native(df)

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                 a
            1  NaN
            2  1.0
            3  2.0
            0  5.0
            >>> func(df_pl)
            shape: (4, 1)
            ┌──────┐
            │ a    │
            │ ---  │
            │ i64  │
            ╞══════╡
            │ null │
            │ 1    │
            │ 2    │
            │ 5    │
            └──────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            ----
            a: [[null,1,2,5]]

            >>> func_descend(df_pd)
                 a
            1  NaN
            0  5.0
            3  2.0
            2  1.0
            >>> func_descend(df_pl)
            shape: (4, 1)
            ┌──────┐
            │ a    │
            │ ---  │
            │ i64  │
            ╞══════╡
            │ null │
            │ 5    │
            │ 2    │
            │ 1    │
            └──────┘
            >>> func_descend(df_pa)
            pyarrow.Table
            a: int64
            ----
            a: [[null,5,2,1]]
        """
        return self.__class__(
            lambda plx: self._call(plx).sort(descending=descending, nulls_last=nulls_last)
        )

    # --- transform ---
    def is_between(
        self, lower_bound: Any, upper_bound: Any, closed: str = "both"
    ) -> Self:
        """
        Check if this expression is between the given lower and upper bounds.

        Arguments:
            lower_bound: Lower bound value.

            upper_bound: Upper bound value.

            closed: Define which sides of the interval are closed (inclusive).

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
            >>> df_pl = pl.DataFrame({"a": [1, 2, 3, 4, 5]})
            >>> df_pa = pa.table({"a": [1, 2, 3, 4, 5]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").is_between(2, 4, "right"))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                   a
            0  False
            1  False
            2   True
            3   True
            4  False
            >>> func(df_pl)
            shape: (5, 1)
            ┌───────┐
            │ a     │
            │ ---   │
            │ bool  │
            ╞═══════╡
            │ false │
            │ false │
            │ true  │
            │ true  │
            │ false │
            └───────┘
            >>> func(df_pa)
            pyarrow.Table
            a: bool
            ----
            a: [[false,false,true,true,false]]
        """
        return self.__class__(
            lambda plx: self._call(plx).is_between(lower_bound, upper_bound, closed)
        )

    def is_in(self, other: Any) -> Self:
        """
        Check if elements of this expression are present in the other iterable.

        Arguments:
            other: iterable

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [1, 2, 9, 10]})
            >>> df_pl = pl.DataFrame({"a": [1, 2, 9, 10]})
            >>> df_pa = pa.table({"a": [1, 2, 9, 10]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(b=nw.col("a").is_in([1, 2]))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                a      b
            0   1   True
            1   2   True
            2   9  False
            3  10  False

            >>> func(df_pl)
            shape: (4, 2)
            ┌─────┬───────┐
            │ a   ┆ b     │
            │ --- ┆ ---   │
            │ i64 ┆ bool  │
            ╞═════╪═══════╡
            │ 1   ┆ true  │
            │ 2   ┆ true  │
            │ 9   ┆ false │
            │ 10  ┆ false │
            └─────┴───────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: bool
            ----
            a: [[1,2,9,10]]
            b: [[true,true,false,false]]
        """
        if isinstance(other, Iterable) and not isinstance(other, (str, bytes)):
            return self.__class__(lambda plx: self._call(plx).is_in(other))
        else:
            msg = "Narwhals `is_in` doesn't accept expressions as an argument, as opposed to Polars. You should provide an iterable instead."
            raise NotImplementedError(msg)

    def filter(self, *predicates: Any) -> Self:
        """
        Filters elements based on a condition, returning a new expression.

        Examples:
            >>> import polars as pl
            >>> import pandas as pd
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame({"a": [2, 3, 4, 5, 6, 7], "b": [10, 11, 12, 13, 14, 15]})
            >>> df_pl = pl.DataFrame({"a": [2, 3, 4, 5, 6, 7], "b": [10, 11, 12, 13, 14, 15]})
            >>> df_pa = pa.table({"a": [2, 3, 4, 5, 6, 7], "b": [10, 11, 12, 13, 14, 15]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(
            ...         nw.col("a").filter(nw.col("a") > 4),
            ...         nw.col("b").filter(nw.col("b") < 13),
            ...     )

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a   b
            3  5  10
            4  6  11
            5  7  12
            >>> func(df_pl)
            shape: (3, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ i64 ┆ i64 │
            ╞═════╪═════╡
            │ 5   ┆ 10  │
            │ 6   ┆ 11  │
            │ 7   ┆ 12  │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[5,6,7]]
            b: [[10,11,12]]
        """
        return self.__class__(
            lambda plx: self._call(plx).filter(
                *[extract_compliant(plx, pred) for pred in flatten(predicates)]
            )
        )

    def is_null(self) -> Self:
        """
        Returns a boolean Series indicating which values are null.

        Notes:
            pandas and Polars handle null values differently. Polars distinguishes
            between NaN and Null, whereas pandas doesn't.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame(
            ...     {"a": [2, 4, None, 3, 5], "b": [2.0, 4.0, float("nan"), 3.0, 5.0]}
            ... )
            >>> df_pl = pl.DataFrame(
            ...     {"a": [2, 4, None, 3, 5], "b": [2.0, 4.0, float("nan"), 3.0, 5.0]}
            ... )
            >>> df_pa = pa.table(
            ...     {"a": [2, 4, None, 3, 5], "b": [2.0, 4.0, float("nan"), 3.0, 5.0]}
            ... )

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         a_is_null=nw.col("a").is_null(), b_is_null=nw.col("b").is_null()
            ...     )

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                 a    b  a_is_null  b_is_null
            0  2.0  2.0      False      False
            1  4.0  4.0      False      False
            2  NaN  NaN       True       True
            3  3.0  3.0      False      False
            4  5.0  5.0      False      False

            >>> func(df_pl)  # nan != null for polars
            shape: (5, 4)
            ┌──────┬─────┬───────────┬───────────┐
            │ a    ┆ b   ┆ a_is_null ┆ b_is_null │
            │ ---  ┆ --- ┆ ---       ┆ ---       │
            │ i64  ┆ f64 ┆ bool      ┆ bool      │
            ╞══════╪═════╪═══════════╪═══════════╡
            │ 2    ┆ 2.0 ┆ false     ┆ false     │
            │ 4    ┆ 4.0 ┆ false     ┆ false     │
            │ null ┆ NaN ┆ true      ┆ false     │
            │ 3    ┆ 3.0 ┆ false     ┆ false     │
            │ 5    ┆ 5.0 ┆ false     ┆ false     │
            └──────┴─────┴───────────┴───────────┘

            >>> func(df_pa)  # nan != null for pyarrow
            pyarrow.Table
            a: int64
            b: double
            a_is_null: bool
            b_is_null: bool
            ----
            a: [[2,4,null,3,5]]
            b: [[2,4,nan,3,5]]
            a_is_null: [[false,false,true,false,false]]
            b_is_null: [[false,false,false,false,false]]
        """
        return self.__class__(lambda plx: self._call(plx).is_null())

    def arg_true(self) -> Self:
        """
        Find elements where boolean expression is True.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> data = {"a": [1, None, None, 2]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            We define a library agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").is_null().arg_true())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a
            1  1
            2  2
            >>> func(df_pl)
            shape: (2, 1)
            ┌─────┐
            │ a   │
            │ --- │
            │ u32 │
            ╞═════╡
            │ 1   │
            │ 2   │
            └─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            ----
            a: [[1,2]]
        """
        return self.__class__(lambda plx: self._call(plx).arg_true())

    def fill_null(
        self,
        value: Any | None = None,
        strategy: Literal["forward", "backward"] | None = None,
        limit: int | None = None,
    ) -> Self:
        """
        Fill null values with given value.

        Arguments:
            value: Value used to fill null values.

            strategy: Strategy used to fill null values.

            limit: Number of consecutive null values to fill when using the 'forward' or 'backward' strategy.

        Notes:
            pandas and Polars handle null values differently. Polars distinguishes
            between NaN and Null, whereas pandas doesn't.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> df_pd = pd.DataFrame(
            ...     {
            ...         "a": [2, 4, None, None, 3, 5],
            ...         "b": [2.0, 4.0, float("nan"), float("nan"), 3.0, 5.0],
            ...     }
            ... )
            >>> df_pl = pl.DataFrame(
            ...     {
            ...         "a": [2, 4, None, None, 3, 5],
            ...         "b": [2.0, 4.0, float("nan"), float("nan"), 3.0, 5.0],
            ...     }
            ... )
            >>> df_pa = pa.table(
            ...     {
            ...         "a": [2, 4, None, None, 3, 5],
            ...         "b": [2.0, 4.0, float("nan"), float("nan"), 3.0, 5.0],
            ...     }
            ... )

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(nw.col("a", "b").fill_null(0))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                 a    b
            0  2.0  2.0
            1  4.0  4.0
            2  0.0  0.0
            3  0.0  0.0
            4  3.0  3.0
            5  5.0  5.0

            >>> func(df_pl)  # nan != null for polars
            shape: (6, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ i64 ┆ f64 │
            ╞═════╪═════╡
            │ 2   ┆ 2.0 │
            │ 4   ┆ 4.0 │
            │ 0   ┆ NaN │
            │ 0   ┆ NaN │
            │ 3   ┆ 3.0 │
            │ 5   ┆ 5.0 │
            └─────┴─────┘

            >>> func(df_pa)  # nan != null for pyarrow
            pyarrow.Table
            a: int64
            b: double
            ----
            a: [[2,4,0,0,3,5]]
            b: [[2,4,nan,nan,3,5]]

            Using a strategy:

            >>> @nw.narwhalify
            ... def func_strategies(df):
            ...     return df.with_columns(
            ...         nw.col("a", "b")
            ...         .fill_null(strategy="forward", limit=1)
            ...         .name.suffix("_filled")
            ...     )

            >>> func_strategies(df_pd)
                 a    b  a_filled  b_filled
            0  2.0  2.0       2.0       2.0
            1  4.0  4.0       4.0       4.0
            2  NaN  NaN       4.0       4.0
            3  NaN  NaN       NaN       NaN
            4  3.0  3.0       3.0       3.0
            5  5.0  5.0       5.0       5.0

            >>> func_strategies(df_pl)  # nan != null for polars
            shape: (6, 4)
            ┌──────┬─────┬──────────┬──────────┐
            │ a    ┆ b   ┆ a_filled ┆ b_filled │
            │ ---  ┆ --- ┆ ---      ┆ ---      │
            │ i64  ┆ f64 ┆ i64      ┆ f64      │
            ╞══════╪═════╪══════════╪══════════╡
            │ 2    ┆ 2.0 ┆ 2        ┆ 2.0      │
            │ 4    ┆ 4.0 ┆ 4        ┆ 4.0      │
            │ null ┆ NaN ┆ 4        ┆ NaN      │
            │ null ┆ NaN ┆ null     ┆ NaN      │
            │ 3    ┆ 3.0 ┆ 3        ┆ 3.0      │
            │ 5    ┆ 5.0 ┆ 5        ┆ 5.0      │
            └──────┴─────┴──────────┴──────────┘

            >>> func_strategies(df_pa)  # nan != null for pyarrow
            pyarrow.Table
            a: int64
            b: double
            a_filled: int64
            b_filled: double
            ----
            a: [[2,4,null,null,3,5]]
            b: [[2,4,nan,nan,3,5]]
            a_filled: [[2,4,4,null,3,5]]
            b_filled: [[2,4,nan,nan,3,5]]
        """
        if value is not None and strategy is not None:
            msg = "cannot specify both `value` and `strategy`"
            raise ValueError(msg)
        if value is None and strategy is None:
            msg = "must specify either a fill `value` or `strategy`"
            raise ValueError(msg)
        if strategy is not None and strategy not in {"forward", "backward"}:
            msg = f"strategy not supported: {strategy}"
            raise ValueError(msg)
        return self.__class__(
            lambda plx: self._call(plx).fill_null(
                value=value, strategy=strategy, limit=limit
            )
        )

    # --- partial reduction ---
    def drop_nulls(self) -> Self:
        """
        Remove missing values.

        Notes:
            pandas and Polars handle null values differently. Polars distinguishes
            between NaN and Null, whereas pandas doesn't.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa

            >>> df_pd = pd.DataFrame({"a": [2.0, 4.0, float("nan"), 3.0, None, 5.0]})
            >>> df_pl = pl.DataFrame({"a": [2.0, 4.0, float("nan"), 3.0, None, 5.0]})
            >>> df_pa = pa.table({"a": [2.0, 4.0, float("nan"), 3.0, None, 5.0]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").drop_nulls())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                 a
            0  2.0
            1  4.0
            3  3.0
            5  5.0
            >>> func(df_pl)  # nan != null for polars
            shape: (5, 1)
            ┌─────┐
            │ a   │
            │ --- │
            │ f64 │
            ╞═════╡
            │ 2.0 │
            │ 4.0 │
            │ NaN │
            │ 3.0 │
            │ 5.0 │
            └─────┘
            >>> func(df_pa)  # nan != null for pyarrow
            pyarrow.Table
            a: double
            ----
            a: [[2,4,nan,3,5]]
        """
        return self.__class__(lambda plx: self._call(plx).drop_nulls())

    def sample(
        self: Self,
        n: int | None = None,
        *,
        fraction: float | None = None,
        with_replacement: bool = False,
        seed: int | None = None,
    ) -> Self:
        """
        Sample randomly from this expression.

        Arguments:
            n: Number of items to return. Cannot be used with fraction.
            fraction: Fraction of items to return. Cannot be used with n.
            with_replacement: Allow values to be sampled more than once.
            seed: Seed for the random number generator. If set to None (default), a random
                seed is generated for each sample operation.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> df_pd = pd.DataFrame({"a": [1, 2, 3]})
            >>> df_pl = pl.DataFrame({"a": [1, 2, 3]})
            >>> df_pa = pa.table({"a": [1, 2, 3]})

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").sample(fraction=1.0, with_replacement=True))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)  # doctest: +SKIP
               a
            2  3
            0  1
            2  3
            >>> func(df_pl)  # doctest: +SKIP
            shape: (3, 1)
            ┌─────┐
            │ a   │
            │ --- │
            │ f64 │
            ╞═════╡
            │ 2   │
            │ 3   │
            │ 3   │
            └─────┘
            >>> func(df_pa)  # doctest: +SKIP
            pyarrow.Table
            a: int64
            ----
            a: [[1,3,3]]
        """
        return self.__class__(
            lambda plx: self._call(plx).sample(
                n, fraction=fraction, with_replacement=with_replacement, seed=seed
            )
        )

    def over(self, *keys: str | Iterable[str]) -> Self:
        """
        Compute expressions over the given groups.

        Arguments:
            keys: Names of columns to compute window expression over.
                  Must be names of columns, as opposed to expressions -
                  so, this is a bit less flexible than Polars' `Expr.over`.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": [1, 2, 3], "b": [1, 1, 2]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(a_min_per_group=nw.col("a").min().over("b"))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a  b  a_min_per_group
            0  1  1                1
            1  2  1                1
            2  3  2                3
            >>> func(df_pl)
            shape: (3, 3)
            ┌─────┬─────┬─────────────────┐
            │ a   ┆ b   ┆ a_min_per_group │
            │ --- ┆ --- ┆ ---             │
            │ i64 ┆ i64 ┆ i64             │
            ╞═════╪═════╪═════════════════╡
            │ 1   ┆ 1   ┆ 1               │
            │ 2   ┆ 1   ┆ 1               │
            │ 3   ┆ 2   ┆ 3               │
            └─────┴─────┴─────────────────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            a_min_per_group: int64
            ----
            a: [[1,2,3]]
            b: [[1,1,2]]
            a_min_per_group: [[1,1,3]]
        """
        return self.__class__(lambda plx: self._call(plx).over(flatten(keys)))

    def is_duplicated(self) -> Self:
        r"""
        Return a boolean mask indicating duplicated values.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": [1, 2, 3, 1], "b": ["a", "a", "b", "c"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.all().is_duplicated())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                   a      b
            0   True   True
            1  False   True
            2  False  False
            3   True  False
            >>> func(df_pl)
            shape: (4, 2)
            ┌───────┬───────┐
            │ a     ┆ b     │
            │ ---   ┆ ---   │
            │ bool  ┆ bool  │
            ╞═══════╪═══════╡
            │ true  ┆ true  │
            │ false ┆ true  │
            │ false ┆ false │
            │ true  ┆ false │
            └───────┴───────┘
            >>> func(df_pa)
            pyarrow.Table
            a: bool
            b: bool
            ----
            a: [[true,false,false,true]]
            b: [[true,true,false,false]]
        """
        return self.__class__(lambda plx: self._call(plx).is_duplicated())

    def is_unique(self) -> Self:
        r"""
        Return a boolean mask indicating unique values.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": [1, 2, 3, 1], "b": ["a", "a", "b", "c"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.all().is_unique())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                   a      b
            0  False  False
            1   True  False
            2   True   True
            3  False   True
            >>> func(df_pl)
            shape: (4, 2)
            ┌───────┬───────┐
            │ a     ┆ b     │
            │ ---   ┆ ---   │
            │ bool  ┆ bool  │
            ╞═══════╪═══════╡
            │ false ┆ false │
            │ true  ┆ false │
            │ true  ┆ true  │
            │ false ┆ true  │
            └───────┴───────┘
            >>> func(df_pa)
            pyarrow.Table
            a: bool
            b: bool
            ----
            a: [[false,true,true,false]]
            b: [[false,false,true,true]]
        """
        return self.__class__(lambda plx: self._call(plx).is_unique())

    def null_count(self) -> Self:
        r"""
        Count null values.

        Notes:
            pandas and Polars handle null values differently. Polars distinguishes
            between NaN and Null, whereas pandas doesn't.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": [1, 2, None, 1], "b": ["a", None, "b", None]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.all().null_count())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a  b
            0  1  2
            >>> func(df_pl)
            shape: (1, 2)
            ┌─────┬─────┐
            │ a   ┆ b   │
            │ --- ┆ --- │
            │ u32 ┆ u32 │
            ╞═════╪═════╡
            │ 1   ┆ 2   │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            b: int64
            ----
            a: [[1]]
            b: [[2]]
        """
        return self.__class__(lambda plx: self._call(plx).null_count())

    def is_first_distinct(self) -> Self:
        r"""
        Return a boolean mask indicating the first occurrence of each distinct value.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": [1, 2, 3, 1], "b": ["a", "a", "b", "c"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.all().is_first_distinct())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                   a      b
            0   True   True
            1   True  False
            2   True   True
            3  False   True
            >>> func(df_pl)
            shape: (4, 2)
            ┌───────┬───────┐
            │ a     ┆ b     │
            │ ---   ┆ ---   │
            │ bool  ┆ bool  │
            ╞═══════╪═══════╡
            │ true  ┆ true  │
            │ true  ┆ false │
            │ true  ┆ true  │
            │ false ┆ true  │
            └───────┴───────┘
            >>> func(df_pa)
            pyarrow.Table
            a: bool
            b: bool
            ----
            a: [[true,true,true,false]]
            b: [[true,false,true,true]]
        """
        return self.__class__(lambda plx: self._call(plx).is_first_distinct())

    def is_last_distinct(self) -> Self:
        r"""Return a boolean mask indicating the last occurrence of each distinct value.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": [1, 2, 3, 1], "b": ["a", "a", "b", "c"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.all().is_last_distinct())

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                   a      b
            0  False  False
            1   True   True
            2   True   True
            3   True   True
            >>> func(df_pl)
            shape: (4, 2)
            ┌───────┬───────┐
            │ a     ┆ b     │
            │ ---   ┆ ---   │
            │ bool  ┆ bool  │
            ╞═══════╪═══════╡
            │ false ┆ false │
            │ true  ┆ true  │
            │ true  ┆ true  │
            │ true  ┆ true  │
            └───────┴───────┘
            >>> func(df_pa)
            pyarrow.Table
            a: bool
            b: bool
            ----
            a: [[false,true,true,true]]
            b: [[false,true,true,true]]
        """
        return self.__class__(lambda plx: self._call(plx).is_last_distinct())

    def quantile(
        self,
        quantile: float,
        interpolation: Literal["nearest", "higher", "lower", "midpoint", "linear"],
    ) -> Self:
        r"""Get quantile value.

        Note:
            - pandas and Polars may have implementation differences for a given interpolation method.
            - [dask](https://docs.dask.org/en/stable/generated/dask.dataframe.Series.quantile.html) has its own method to approximate quantile and it doesn't implement 'nearest', 'higher', 'lower', 'midpoint'
            as interpolation method - use 'linear' which is closest to the native 'dask' - method.

        Arguments:
            quantile: Quantile between 0.0 and 1.0.
            interpolation: Interpolation method.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": list(range(50)), "b": list(range(50, 100))}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a", "b").quantile(0.5, interpolation="linear"))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                  a     b
            0  24.5  74.5

            >>> func(df_pl)
            shape: (1, 2)
            ┌──────┬──────┐
            │ a    ┆ b    │
            │ ---  ┆ ---  │
            │ f64  ┆ f64  │
            ╞══════╪══════╡
            │ 24.5 ┆ 74.5 │
            └──────┴──────┘
            >>> func(df_pa)
            pyarrow.Table
            a: double
            b: double
            ----
            a: [[24.5]]
            b: [[74.5]]
        """
        return self.__class__(
            lambda plx: self._call(plx).quantile(quantile, interpolation)
        )

    def head(self, n: int = 10) -> Self:
        r"""
        Get the first `n` rows.

        Arguments:
            n: Number of rows to return.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": list(range(10))}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function that returns the first 3 rows:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").head(3))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a
            0  0
            1  1
            2  2
            >>> func(df_pl)
            shape: (3, 1)
            ┌─────┐
            │ a   │
            │ --- │
            │ i64 │
            ╞═════╡
            │ 0   │
            │ 1   │
            │ 2   │
            └─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            ----
            a: [[0,1,2]]
        """
        return self.__class__(lambda plx: self._call(plx).head(n))

    def tail(self, n: int = 10) -> Self:
        r"""
        Get the last `n` rows.

        Arguments:
            n: Number of rows to return.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": list(range(10))}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function that returns the last 3 rows:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").tail(3))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a
            7  7
            8  8
            9  9
            >>> func(df_pl)
            shape: (3, 1)
            ┌─────┐
            │ a   │
            │ --- │
            │ i64 │
            ╞═════╡
            │ 7   │
            │ 8   │
            │ 9   │
            └─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            ----
            a: [[7,8,9]]
        """
        return self.__class__(lambda plx: self._call(plx).tail(n))

    def round(self, decimals: int = 0) -> Self:
        r"""
        Round underlying floating point data by `decimals` digits.

        Arguments:
            decimals: Number of decimals to round by.

        Notes:
            For values exactly halfway between rounded decimal values pandas behaves differently than Polars and Arrow.

            pandas rounds to the nearest even value (e.g. -0.5 and 0.5 round to 0.0, 1.5 and 2.5 round to 2.0, 3.5 and
            4.5 to 4.0, etc..).

            Polars and Arrow round away from 0 (e.g. -0.5 to -1.0, 0.5 to 1.0, 1.5 to 2.0, 2.5 to 3.0, etc..).


        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": [1.12345, 2.56789, 3.901234]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function that rounds to the first decimal:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").round(1))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
                 a
            0  1.1
            1  2.6
            2  3.9
            >>> func(df_pl)
            shape: (3, 1)
            ┌─────┐
            │ a   │
            │ --- │
            │ f64 │
            ╞═════╡
            │ 1.1 │
            │ 2.6 │
            │ 3.9 │
            └─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: double
            ----
            a: [[1.1,2.6,3.9]]
        """
        return self.__class__(lambda plx: self._call(plx).round(decimals))

    def len(self) -> Self:
        r"""
        Return the number of elements in the column.

        Null values count towards the total.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": ["x", "y", "z"], "b": [1, 2, 1]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function that computes the len over different values of "b" column:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(
            ...         nw.col("a").filter(nw.col("b") == 1).len().alias("a1"),
            ...         nw.col("a").filter(nw.col("b") == 2).len().alias("a2"),
            ...     )

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a1  a2
            0   2   1
            >>> func(df_pl)
            shape: (1, 2)
            ┌─────┬─────┐
            │ a1  ┆ a2  │
            │ --- ┆ --- │
            │ u32 ┆ u32 │
            ╞═════╪═════╡
            │ 2   ┆ 1   │
            └─────┴─────┘
            >>> func(df_pa)
            pyarrow.Table
            a1: int64
            a2: int64
            ----
            a1: [[2]]
            a2: [[1]]
        """
        return self.__class__(lambda plx: self._call(plx).len())

    def gather_every(self: Self, n: int, offset: int = 0) -> Self:
        r"""
        Take every nth value in the Series and return as new Series.

        Arguments:
            n: Gather every *n*-th row.
            offset: Starting index.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"a": [1, 2, 3, 4], "b": [5, 6, 7, 8]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function in which gather every 2 rows,
            starting from a offset of 1:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").gather_every(n=2, offset=1))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a
            1  2
            3  4
            >>> func(df_pl)
            shape: (2, 1)
            ┌─────┐
            │ a   │
            │ --- │
            │ i64 │
            ╞═════╡
            │ 2   │
            │ 4   │
            └─────┘
            >>> func(df_pa)
            pyarrow.Table
            a: int64
            ----
            a: [[2,4]]
        """
        return self.__class__(
            lambda plx: self._call(plx).gather_every(n=n, offset=offset)
        )

    # need to allow numeric typing
    # TODO @aivanoved: make type alias for numeric type
    def clip(
        self,
        lower_bound: Any | None = None,
        upper_bound: Any | None = None,
    ) -> Self:
        r"""
        Clip values in the Series.

        Arguments:
            lower_bound: Lower bound value.
            upper_bound: Upper bound value.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw

            >>> s = [1, 2, 3]
            >>> df_pd = pd.DataFrame({"s": s})
            >>> df_pl = pl.DataFrame({"s": s})
            >>> df_pa = pa.table({"s": s})

            We define a library agnostic function:

            >>> @nw.narwhalify
            ... def func_lower(df):
            ...     return df.select(nw.col("s").clip(2))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func_lower`:

            >>> func_lower(df_pd)
               s
            0  2
            1  2
            2  3
            >>> func_lower(df_pl)
            shape: (3, 1)
            ┌─────┐
            │ s   │
            │ --- │
            │ i64 │
            ╞═════╡
            │ 2   │
            │ 2   │
            │ 3   │
            └─────┘
            >>> func_lower(df_pa)
            pyarrow.Table
            s: int64
            ----
            s: [[2,2,3]]

            We define another library agnostic function:

            >>> @nw.narwhalify
            ... def func_upper(df):
            ...     return df.select(nw.col("s").clip(upper_bound=2))

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func_upper`:

            >>> func_upper(df_pd)
               s
            0  1
            1  2
            2  2
            >>> func_upper(df_pl)
            shape: (3, 1)
            ┌─────┐
            │ s   │
            │ --- │
            │ i64 │
            ╞═════╡
            │ 1   │
            │ 2   │
            │ 2   │
            └─────┘
            >>> func_upper(df_pa)
            pyarrow.Table
            s: int64
            ----
            s: [[1,2,2]]

            We can have both at the same time

            >>> s = [-1, 1, -3, 3, -5, 5]
            >>> df_pd = pd.DataFrame({"s": s})
            >>> df_pl = pl.DataFrame({"s": s})
            >>> df_pa = pa.table({"s": s})

            We define a library agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("s").clip(-1, 3))

            We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               s
            0 -1
            1  1
            2 -1
            3  3
            4 -1
            5  3
            >>> func(df_pl)
            shape: (6, 1)
            ┌─────┐
            │ s   │
            │ --- │
            │ i64 │
            ╞═════╡
            │ -1  │
            │ 1   │
            │ -1  │
            │ 3   │
            │ -1  │
            │ 3   │
            └─────┘
            >>> func(df_pa)
            pyarrow.Table
            s: int64
            ----
            s: [[-1,1,-1,3,-1,3]]
        """
        return self.__class__(lambda plx: self._call(plx).clip(lower_bound, upper_bound))

    def mode(self: Self) -> Self:
        r"""Compute the most occurring value(s).

        Can return multiple values.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw

            >>> data = {
            ...     "a": [1, 1, 2, 3],
            ...     "b": [1, 1, 2, 2],
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            We define a library agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").mode()).sort("a")

            We can then pass any supported library such as Pandas, Polars, or PyArrow to `func`:

            >>> func(df_pd)
               a
            0  1

            >>> func(df_pl)
            shape: (1, 1)
            ┌─────┐
            │ a   │
            │ --- │
            │ i64 │
            ╞═════╡
            │ 1   │
            └─────┘

            >>> func(df_pa)
            pyarrow.Table
            a: int64
            ----
            a: [[1]]
        """
        return self.__class__(lambda plx: self._call(plx).mode())

    @property
    def str(self: Self) -> ExprStringNamespace[Self]:
        return ExprStringNamespace(self)

    @property
    def dt(self: Self) -> ExprDateTimeNamespace[Self]:
        return ExprDateTimeNamespace(self)

    @property
    def cat(self: Self) -> ExprCatNamespace[Self]:
        return ExprCatNamespace(self)

    @property
    def name(self: Self) -> ExprNameNamespace[Self]:
        return ExprNameNamespace(self)


T = TypeVar("T", bound=Expr)


class ExprCatNamespace(Generic[T]):
    def __init__(self: Self, expr: T) -> None:
        self._expr = expr

    def get_categories(self: Self) -> T:
        """
        Get unique categories from column.

        Examples:
            Let's create some dataframes:

            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"fruits": ["apple", "mango", "mango"]}
            >>> df_pd = pd.DataFrame(data, dtype="category")
            >>> df_pl = pl.DataFrame(data, schema={"fruits": pl.Categorical})

            We define a dataframe-agnostic function to get unique categories
            from column 'fruits':

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("fruits").cat.get_categories())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
              fruits
            0  apple
            1  mango
            >>> func(df_pl)
            shape: (2, 1)
            ┌────────┐
            │ fruits │
            │ ---    │
            │ str    │
            ╞════════╡
            │ apple  │
            │ mango  │
            └────────┘
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).cat.get_categories()
        )


class ExprStringNamespace(Generic[T]):
    def __init__(self: Self, expr: T) -> None:
        self._expr = expr

    def len_chars(self: Self) -> T:
        r"""
        Return the length of each string as the number of characters.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"words": ["foo", "Café", "345", "東京", None]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(words_len=nw.col("words").str.len_chars())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
              words  words_len
            0   foo        3.0
            1  Café        4.0
            2   345        3.0
            3    東京        2.0
            4  None        NaN

            >>> func(df_pl)
            shape: (5, 2)
            ┌───────┬───────────┐
            │ words ┆ words_len │
            │ ---   ┆ ---       │
            │ str   ┆ u32       │
            ╞═══════╪═══════════╡
            │ foo   ┆ 3         │
            │ Café  ┆ 4         │
            │ 345   ┆ 3         │
            │ 東京  ┆ 2         │
            │ null  ┆ null      │
            └───────┴───────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).str.len_chars())

    def replace(
        self, pattern: str, value: str, *, literal: bool = False, n: int = 1
    ) -> T:
        r"""
        Replace first matching regex/literal substring with a new string value.

        Arguments:
            pattern: A valid regular expression pattern.
            value: String that will replace the matched substring.
            literal: Treat `pattern` as a literal string.
            n: Number of matches to replace.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"foo": ["123abc", "abc abc123"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     df = df.with_columns(replaced=nw.col("foo").str.replace("abc", ""))
            ...     return df.to_dict(as_series=False)

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
            {'foo': ['123abc', 'abc abc123'], 'replaced': ['123', ' abc123']}

            >>> func(df_pl)
            {'foo': ['123abc', 'abc abc123'], 'replaced': ['123', ' abc123']}

        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).str.replace(
                pattern, value, literal=literal, n=n
            )
        )

    def replace_all(self: Self, pattern: str, value: str, *, literal: bool = False) -> T:
        r"""
        Replace all matching regex/literal substring with a new string value.

        Arguments:
            pattern: A valid regular expression pattern.
            value: String that will replace the matched substring.
            literal: Treat `pattern` as a literal string.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"foo": ["123abc", "abc abc123"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     df = df.with_columns(replaced=nw.col("foo").str.replace_all("abc", ""))
            ...     return df.to_dict(as_series=False)

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
            {'foo': ['123abc', 'abc abc123'], 'replaced': ['123', ' 123']}

            >>> func(df_pl)
            {'foo': ['123abc', 'abc abc123'], 'replaced': ['123', ' 123']}

        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).str.replace_all(
                pattern, value, literal=literal
            )
        )

    def strip_chars(self: Self, characters: str | None = None) -> T:
        r"""
        Remove leading and trailing characters.

        Arguments:
            characters: The set of characters to be removed. All combinations of this set of characters will be stripped from the start and end of the string. If set to None (default), all leading and trailing whitespace is removed instead.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"fruits": ["apple", "\nmango"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     df = df.with_columns(stripped=nw.col("fruits").str.strip_chars())
            ...     return df.to_dict(as_series=False)

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
            {'fruits': ['apple', '\nmango'], 'stripped': ['apple', 'mango']}

            >>> func(df_pl)
            {'fruits': ['apple', '\nmango'], 'stripped': ['apple', 'mango']}
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).str.strip_chars(characters)
        )

    def starts_with(self: Self, prefix: str) -> T:
        r"""
        Check if string values start with a substring.

        Arguments:
            prefix: prefix substring

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"fruits": ["apple", "mango", None]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(has_prefix=nw.col("fruits").str.starts_with("app"))

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
              fruits has_prefix
            0  apple       True
            1  mango      False
            2   None       None

            >>> func(df_pl)
            shape: (3, 2)
            ┌────────┬────────────┐
            │ fruits ┆ has_prefix │
            │ ---    ┆ ---        │
            │ str    ┆ bool       │
            ╞════════╪════════════╡
            │ apple  ┆ true       │
            │ mango  ┆ false      │
            │ null   ┆ null       │
            └────────┴────────────┘
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).str.starts_with(prefix)
        )

    def ends_with(self: Self, suffix: str) -> T:
        r"""
        Check if string values end with a substring.

        Arguments:
            suffix: suffix substring

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"fruits": ["apple", "mango", None]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(has_suffix=nw.col("fruits").str.ends_with("ngo"))

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
              fruits has_suffix
            0  apple      False
            1  mango       True
            2   None       None

            >>> func(df_pl)
            shape: (3, 2)
            ┌────────┬────────────┐
            │ fruits ┆ has_suffix │
            │ ---    ┆ ---        │
            │ str    ┆ bool       │
            ╞════════╪════════════╡
            │ apple  ┆ false      │
            │ mango  ┆ true       │
            │ null   ┆ null       │
            └────────┴────────────┘
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).str.ends_with(suffix)
        )

    def contains(self: Self, pattern: str, *, literal: bool = False) -> T:
        r"""
        Check if string contains a substring that matches a pattern.

        Arguments:
            pattern: A Character sequence or valid regular expression pattern.
            literal: If True, treats the pattern as a literal string.
                     If False, assumes the pattern is a regular expression.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"pets": ["cat", "dog", "rabbit and parrot", "dove", None]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         default_match=nw.col("pets").str.contains("parrot|Dove"),
            ...         case_insensitive_match=nw.col("pets").str.contains("(?i)parrot|Dove"),
            ...         literal_match=nw.col("pets").str.contains(
            ...             "parrot|Dove", literal=True
            ...         ),
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                            pets default_match case_insensitive_match literal_match
            0                cat         False                  False         False
            1                dog         False                  False         False
            2  rabbit and parrot          True                   True         False
            3               dove         False                   True         False
            4               None          None                   None          None
            >>> func(df_pl)
            shape: (5, 4)
            ┌───────────────────┬───────────────┬────────────────────────┬───────────────┐
            │ pets              ┆ default_match ┆ case_insensitive_match ┆ literal_match │
            │ ---               ┆ ---           ┆ ---                    ┆ ---           │
            │ str               ┆ bool          ┆ bool                   ┆ bool          │
            ╞═══════════════════╪═══════════════╪════════════════════════╪═══════════════╡
            │ cat               ┆ false         ┆ false                  ┆ false         │
            │ dog               ┆ false         ┆ false                  ┆ false         │
            │ rabbit and parrot ┆ true          ┆ true                   ┆ false         │
            │ dove              ┆ false         ┆ true                   ┆ false         │
            │ null              ┆ null          ┆ null                   ┆ null          │
            └───────────────────┴───────────────┴────────────────────────┴───────────────┘
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).str.contains(pattern, literal=literal)
        )

    def slice(self: Self, offset: int, length: int | None = None) -> T:
        r"""
        Create subslices of the string values of an expression.

        Arguments:
            offset: Start index. Negative indexing is supported.
            length: Length of the slice. If set to `None` (default), the slice is taken to the
                end of the string.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"s": ["pear", None, "papaya", "dragonfruit"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(s_sliced=nw.col("s").str.slice(4, length=3))

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)  # doctest: +NORMALIZE_WHITESPACE
                         s s_sliced
            0         pear
            1         None     None
            2       papaya       ya
            3  dragonfruit      onf

            >>> func(df_pl)
            shape: (4, 2)
            ┌─────────────┬──────────┐
            │ s           ┆ s_sliced │
            │ ---         ┆ ---      │
            │ str         ┆ str      │
            ╞═════════════╪══════════╡
            │ pear        ┆          │
            │ null        ┆ null     │
            │ papaya      ┆ ya       │
            │ dragonfruit ┆ onf      │
            └─────────────┴──────────┘

            Using negative indexes:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(s_sliced=nw.col("s").str.slice(-3))

            >>> func(df_pd)
                         s s_sliced
            0         pear      ear
            1         None     None
            2       papaya      aya
            3  dragonfruit      uit

            >>> func(df_pl)
            shape: (4, 2)
            ┌─────────────┬──────────┐
            │ s           ┆ s_sliced │
            │ ---         ┆ ---      │
            │ str         ┆ str      │
            ╞═════════════╪══════════╡
            │ pear        ┆ ear      │
            │ null        ┆ null     │
            │ papaya      ┆ aya      │
            │ dragonfruit ┆ uit      │
            └─────────────┴──────────┘
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).str.slice(offset=offset, length=length)
        )

    def head(self: Self, n: int = 5) -> T:
        r"""
        Take the first n elements of each string.

        Arguments:
            n: Number of elements to take. Negative indexing is **not** supported.

        Notes:
            If the length of the string has fewer than `n` characters, the full string is returned.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"lyrics": ["Atatata", "taata", "taatatata", "zukkyun"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(lyrics_head=nw.col("lyrics").str.head())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                  lyrics lyrics_head
            0    Atatata       Atata
            1      taata       taata
            2  taatatata       taata
            3    zukkyun       zukky

            >>> func(df_pl)
            shape: (4, 2)
            ┌───────────┬─────────────┐
            │ lyrics    ┆ lyrics_head │
            │ ---       ┆ ---         │
            │ str       ┆ str         │
            ╞═══════════╪═════════════╡
            │ Atatata   ┆ Atata       │
            │ taata     ┆ taata       │
            │ taatatata ┆ taata       │
            │ zukkyun   ┆ zukky       │
            └───────────┴─────────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).str.slice(0, n))

    def tail(self: Self, n: int = 5) -> T:
        r"""
        Take the last n elements of each string.

        Arguments:
            n: Number of elements to take. Negative indexing is **not** supported.

        Notes:
            If the length of the string has fewer than `n` characters, the full string is returned.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"lyrics": ["Atatata", "taata", "taatatata", "zukkyun"]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(lyrics_tail=nw.col("lyrics").str.tail())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                  lyrics lyrics_tail
            0    Atatata       atata
            1      taata       taata
            2  taatatata       atata
            3    zukkyun       kkyun

            >>> func(df_pl)
            shape: (4, 2)
            ┌───────────┬─────────────┐
            │ lyrics    ┆ lyrics_tail │
            │ ---       ┆ ---         │
            │ str       ┆ str         │
            ╞═══════════╪═════════════╡
            │ Atatata   ┆ atata       │
            │ taata     ┆ taata       │
            │ taatatata ┆ atata       │
            │ zukkyun   ┆ kkyun       │
            └───────────┴─────────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).str.slice(-n))

    def to_datetime(self: Self, format: str | None = None) -> T:  # noqa: A002
        """
        Convert to Datetime dtype.

        Notes:
            pandas defaults to nanosecond time unit, Polars to microsecond.
            Prior to pandas 2.0, nanoseconds were the only time unit supported
            in pandas, with no ability to set any other one. The ability to
            set the time unit in pandas, if the version permits, will arrive.

        Warning:
            As different backends auto-infer format in different ways, if `format=None`
            there is no guarantee that the result will be equal.

        Arguments:
            format: Format to use for conversion. If set to None (default), the format is
                inferred from the data.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> import narwhals as nw
            >>> data = ["2020-01-01", "2020-01-02"]
            >>> df_pd = pd.DataFrame({"a": data})
            >>> df_pl = pl.DataFrame({"a": data})
            >>> df_pa = pa.table({"a": data})

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").str.to_datetime(format="%Y-%m-%d"))

            We can then pass any supported library such as pandas, Polars, or PyArrow:

            >>> func(df_pd)
                       a
            0 2020-01-01
            1 2020-01-02
            >>> func(df_pl)
            shape: (2, 1)
            ┌─────────────────────┐
            │ a                   │
            │ ---                 │
            │ datetime[μs]        │
            ╞═════════════════════╡
            │ 2020-01-01 00:00:00 │
            │ 2020-01-02 00:00:00 │
            └─────────────────────┘
            >>> func(df_pa)
            pyarrow.Table
            a: timestamp[us]
            ----
            a: [[2020-01-01 00:00:00.000000,2020-01-02 00:00:00.000000]]
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).str.to_datetime(format=format)
        )

    def to_uppercase(self: Self) -> T:
        r"""
        Transform string to uppercase variant.

        Notes:
            The PyArrow backend will convert 'ß' to 'ẞ' instead of 'SS'.
            For more info see [the related issue](https://github.com/apache/arrow/issues/34599).
            There may be other unicode-edge-case-related variations across implementations.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"fruits": ["apple", "mango", None]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(upper_col=nw.col("fruits").str.to_uppercase())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
              fruits upper_col
            0  apple     APPLE
            1  mango     MANGO
            2   None      None

            >>> func(df_pl)
            shape: (3, 2)
            ┌────────┬───────────┐
            │ fruits ┆ upper_col │
            │ ---    ┆ ---       │
            │ str    ┆ str       │
            ╞════════╪═══════════╡
            │ apple  ┆ APPLE     │
            │ mango  ┆ MANGO     │
            │ null   ┆ null      │
            └────────┴───────────┘

        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).str.to_uppercase())

    def to_lowercase(self: Self) -> T:
        r"""
        Transform string to lowercase variant.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = {"fruits": ["APPLE", "MANGO", None]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(lower_col=nw.col("fruits").str.to_lowercase())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
              fruits lower_col
            0  APPLE     apple
            1  MANGO     mango
            2   None      None

            >>> func(df_pl)
            shape: (3, 2)
            ┌────────┬───────────┐
            │ fruits ┆ lower_col │
            │ ---    ┆ ---       │
            │ str    ┆ str       │
            ╞════════╪═══════════╡
            │ APPLE  ┆ apple     │
            │ MANGO  ┆ mango     │
            │ null   ┆ null      │
            └────────┴───────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).str.to_lowercase())


class ExprDateTimeNamespace(Generic[T]):
    def __init__(self: Self, expr: T) -> None:
        self._expr = expr

    def date(self: Self) -> T:
        """
        Extract the date from underlying DateTime representation.

        Raises:
            NotImplementedError: If pandas default backend is being used.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {"a": [datetime(2012, 1, 7, 10, 20), datetime(2023, 3, 10, 11, 32)]}
            >>> df_pd = pd.DataFrame(data).convert_dtypes(dtype_backend="pyarrow")
            >>> df_pl = pl.DataFrame(data)

            We define a library agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").dt.date())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                        a
            0  2012-01-07
            1  2023-03-10

            >>> func(df_pl)  # docetst
            shape: (2, 1)
            ┌────────────┐
            │ a          │
            │ ---        │
            │ date       │
            ╞════════════╡
            │ 2012-01-07 │
            │ 2023-03-10 │
            └────────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.date())

    def year(self: Self) -> T:
        """
        Extract year from underlying DateTime representation.

        Returns the year number in the calendar date.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {
            ...     "datetime": [
            ...         datetime(1978, 6, 1),
            ...         datetime(2024, 12, 13),
            ...         datetime(2065, 1, 1),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(nw.col("datetime").dt.year().alias("year"))

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                datetime  year
            0 1978-06-01  1978
            1 2024-12-13  2024
            2 2065-01-01  2065
            >>> func(df_pl)
            shape: (3, 2)
            ┌─────────────────────┬──────┐
            │ datetime            ┆ year │
            │ ---                 ┆ ---  │
            │ datetime[μs]        ┆ i32  │
            ╞═════════════════════╪══════╡
            │ 1978-06-01 00:00:00 ┆ 1978 │
            │ 2024-12-13 00:00:00 ┆ 2024 │
            │ 2065-01-01 00:00:00 ┆ 2065 │
            └─────────────────────┴──────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.year())

    def month(self: Self) -> T:
        """
        Extract month from underlying DateTime representation.

        Returns the month number starting from 1. The return value ranges from 1 to 12.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {
            ...     "datetime": [
            ...         datetime(1978, 6, 1),
            ...         datetime(2024, 12, 13),
            ...         datetime(2065, 1, 1),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         nw.col("datetime").dt.year().alias("year"),
            ...         nw.col("datetime").dt.month().alias("month"),
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                datetime  year  month
            0 1978-06-01  1978      6
            1 2024-12-13  2024     12
            2 2065-01-01  2065      1
            >>> func(df_pl)
            shape: (3, 3)
            ┌─────────────────────┬──────┬───────┐
            │ datetime            ┆ year ┆ month │
            │ ---                 ┆ ---  ┆ ---   │
            │ datetime[μs]        ┆ i32  ┆ i8    │
            ╞═════════════════════╪══════╪═══════╡
            │ 1978-06-01 00:00:00 ┆ 1978 ┆ 6     │
            │ 2024-12-13 00:00:00 ┆ 2024 ┆ 12    │
            │ 2065-01-01 00:00:00 ┆ 2065 ┆ 1     │
            └─────────────────────┴──────┴───────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.month())

    def day(self: Self) -> T:
        """
        Extract day from underlying DateTime representation.

        Returns the day of month starting from 1. The return value ranges from 1 to 31. (The last day of month differs by months.)

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {
            ...     "datetime": [
            ...         datetime(1978, 6, 1),
            ...         datetime(2024, 12, 13),
            ...         datetime(2065, 1, 1),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         nw.col("datetime").dt.year().alias("year"),
            ...         nw.col("datetime").dt.month().alias("month"),
            ...         nw.col("datetime").dt.day().alias("day"),
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                datetime  year  month  day
            0 1978-06-01  1978      6    1
            1 2024-12-13  2024     12   13
            2 2065-01-01  2065      1    1
            >>> func(df_pl)
            shape: (3, 4)
            ┌─────────────────────┬──────┬───────┬─────┐
            │ datetime            ┆ year ┆ month ┆ day │
            │ ---                 ┆ ---  ┆ ---   ┆ --- │
            │ datetime[μs]        ┆ i32  ┆ i8    ┆ i8  │
            ╞═════════════════════╪══════╪═══════╪═════╡
            │ 1978-06-01 00:00:00 ┆ 1978 ┆ 6     ┆ 1   │
            │ 2024-12-13 00:00:00 ┆ 2024 ┆ 12    ┆ 13  │
            │ 2065-01-01 00:00:00 ┆ 2065 ┆ 1     ┆ 1   │
            └─────────────────────┴──────┴───────┴─────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.day())

    def hour(self: Self) -> T:
        """
        Extract hour from underlying DateTime representation.

        Returns the hour number from 0 to 23.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {
            ...     "datetime": [
            ...         datetime(1978, 1, 1, 1),
            ...         datetime(2024, 10, 13, 5),
            ...         datetime(2065, 1, 1, 10),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(nw.col("datetime").dt.hour().alias("hour"))

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                         datetime  hour
            0 1978-01-01 01:00:00     1
            1 2024-10-13 05:00:00     5
            2 2065-01-01 10:00:00    10
            >>> func(df_pl)
            shape: (3, 2)
            ┌─────────────────────┬──────┐
            │ datetime            ┆ hour │
            │ ---                 ┆ ---  │
            │ datetime[μs]        ┆ i8   │
            ╞═════════════════════╪══════╡
            │ 1978-01-01 01:00:00 ┆ 1    │
            │ 2024-10-13 05:00:00 ┆ 5    │
            │ 2065-01-01 10:00:00 ┆ 10   │
            └─────────────────────┴──────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.hour())

    def minute(self: Self) -> T:
        """
        Extract minutes from underlying DateTime representation.

        Returns the minute number from 0 to 59.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {
            ...     "datetime": [
            ...         datetime(1978, 1, 1, 1, 1),
            ...         datetime(2024, 10, 13, 5, 30),
            ...         datetime(2065, 1, 1, 10, 20),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         nw.col("datetime").dt.hour().alias("hour"),
            ...         nw.col("datetime").dt.minute().alias("minute"),
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                         datetime  hour  minute
            0 1978-01-01 01:01:00     1       1
            1 2024-10-13 05:30:00     5      30
            2 2065-01-01 10:20:00    10      20
            >>> func(df_pl)
            shape: (3, 3)
            ┌─────────────────────┬──────┬────────┐
            │ datetime            ┆ hour ┆ minute │
            │ ---                 ┆ ---  ┆ ---    │
            │ datetime[μs]        ┆ i8   ┆ i8     │
            ╞═════════════════════╪══════╪════════╡
            │ 1978-01-01 01:01:00 ┆ 1    ┆ 1      │
            │ 2024-10-13 05:30:00 ┆ 5    ┆ 30     │
            │ 2065-01-01 10:20:00 ┆ 10   ┆ 20     │
            └─────────────────────┴──────┴────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.minute())

    def second(self: Self) -> T:
        """
        Extract seconds from underlying DateTime representation.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {
            ...     "datetime": [
            ...         datetime(1978, 1, 1, 1, 1, 1),
            ...         datetime(2024, 10, 13, 5, 30, 14),
            ...         datetime(2065, 1, 1, 10, 20, 30),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         nw.col("datetime").dt.hour().alias("hour"),
            ...         nw.col("datetime").dt.minute().alias("minute"),
            ...         nw.col("datetime").dt.second().alias("second"),
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                         datetime  hour  minute  second
            0 1978-01-01 01:01:01     1       1       1
            1 2024-10-13 05:30:14     5      30      14
            2 2065-01-01 10:20:30    10      20      30
            >>> func(df_pl)
            shape: (3, 4)
            ┌─────────────────────┬──────┬────────┬────────┐
            │ datetime            ┆ hour ┆ minute ┆ second │
            │ ---                 ┆ ---  ┆ ---    ┆ ---    │
            │ datetime[μs]        ┆ i8   ┆ i8     ┆ i8     │
            ╞═════════════════════╪══════╪════════╪════════╡
            │ 1978-01-01 01:01:01 ┆ 1    ┆ 1      ┆ 1      │
            │ 2024-10-13 05:30:14 ┆ 5    ┆ 30     ┆ 14     │
            │ 2065-01-01 10:20:30 ┆ 10   ┆ 20     ┆ 30     │
            └─────────────────────┴──────┴────────┴────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.second())

    def millisecond(self: Self) -> T:
        """
        Extract milliseconds from underlying DateTime representation.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {
            ...     "datetime": [
            ...         datetime(1978, 1, 1, 1, 1, 1, 0),
            ...         datetime(2024, 10, 13, 5, 30, 14, 505000),
            ...         datetime(2065, 1, 1, 10, 20, 30, 67000),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         nw.col("datetime").dt.hour().alias("hour"),
            ...         nw.col("datetime").dt.minute().alias("minute"),
            ...         nw.col("datetime").dt.second().alias("second"),
            ...         nw.col("datetime").dt.millisecond().alias("millisecond"),
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                             datetime  hour  minute  second  millisecond
            0 1978-01-01 01:01:01.000     1       1       1            0
            1 2024-10-13 05:30:14.505     5      30      14          505
            2 2065-01-01 10:20:30.067    10      20      30           67
            >>> func(df_pl)
            shape: (3, 5)
            ┌─────────────────────────┬──────┬────────┬────────┬─────────────┐
            │ datetime                ┆ hour ┆ minute ┆ second ┆ millisecond │
            │ ---                     ┆ ---  ┆ ---    ┆ ---    ┆ ---         │
            │ datetime[μs]            ┆ i8   ┆ i8     ┆ i8     ┆ i32         │
            ╞═════════════════════════╪══════╪════════╪════════╪═════════════╡
            │ 1978-01-01 01:01:01     ┆ 1    ┆ 1      ┆ 1      ┆ 0           │
            │ 2024-10-13 05:30:14.505 ┆ 5    ┆ 30     ┆ 14     ┆ 505         │
            │ 2065-01-01 10:20:30.067 ┆ 10   ┆ 20     ┆ 30     ┆ 67          │
            └─────────────────────────┴──────┴────────┴────────┴─────────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.millisecond())

    def microsecond(self: Self) -> T:
        """
        Extract microseconds from underlying DateTime representation.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {
            ...     "datetime": [
            ...         datetime(1978, 1, 1, 1, 1, 1, 0),
            ...         datetime(2024, 10, 13, 5, 30, 14, 505000),
            ...         datetime(2065, 1, 1, 10, 20, 30, 67000),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         nw.col("datetime").dt.hour().alias("hour"),
            ...         nw.col("datetime").dt.minute().alias("minute"),
            ...         nw.col("datetime").dt.second().alias("second"),
            ...         nw.col("datetime").dt.microsecond().alias("microsecond"),
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                             datetime  hour  minute  second  microsecond
            0 1978-01-01 01:01:01.000     1       1       1            0
            1 2024-10-13 05:30:14.505     5      30      14       505000
            2 2065-01-01 10:20:30.067    10      20      30        67000
            >>> func(df_pl)
            shape: (3, 5)
            ┌─────────────────────────┬──────┬────────┬────────┬─────────────┐
            │ datetime                ┆ hour ┆ minute ┆ second ┆ microsecond │
            │ ---                     ┆ ---  ┆ ---    ┆ ---    ┆ ---         │
            │ datetime[μs]            ┆ i8   ┆ i8     ┆ i8     ┆ i32         │
            ╞═════════════════════════╪══════╪════════╪════════╪═════════════╡
            │ 1978-01-01 01:01:01     ┆ 1    ┆ 1      ┆ 1      ┆ 0           │
            │ 2024-10-13 05:30:14.505 ┆ 5    ┆ 30     ┆ 14     ┆ 505000      │
            │ 2065-01-01 10:20:30.067 ┆ 10   ┆ 20     ┆ 30     ┆ 67000       │
            └─────────────────────────┴──────┴────────┴────────┴─────────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.microsecond())

    def nanosecond(self: Self) -> T:
        """
        Extract Nanoseconds from underlying DateTime representation

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {
            ...     "datetime": [
            ...         datetime(1978, 1, 1, 1, 1, 1, 0),
            ...         datetime(2024, 10, 13, 5, 30, 14, 500000),
            ...         datetime(2065, 1, 1, 10, 20, 30, 60000),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         nw.col("datetime").dt.hour().alias("hour"),
            ...         nw.col("datetime").dt.minute().alias("minute"),
            ...         nw.col("datetime").dt.second().alias("second"),
            ...         nw.col("datetime").dt.nanosecond().alias("nanosecond"),
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                             datetime  hour  minute  second  nanosecond
            0 1978-01-01 01:01:01.000     1       1       1           0
            1 2024-10-13 05:30:14.500     5      30      14   500000000
            2 2065-01-01 10:20:30.060    10      20      30    60000000
            >>> func(df_pl)
            shape: (3, 5)
            ┌─────────────────────────┬──────┬────────┬────────┬────────────┐
            │ datetime                ┆ hour ┆ minute ┆ second ┆ nanosecond │
            │ ---                     ┆ ---  ┆ ---    ┆ ---    ┆ ---        │
            │ datetime[μs]            ┆ i8   ┆ i8     ┆ i8     ┆ i32        │
            ╞═════════════════════════╪══════╪════════╪════════╪════════════╡
            │ 1978-01-01 01:01:01     ┆ 1    ┆ 1      ┆ 1      ┆ 0          │
            │ 2024-10-13 05:30:14.500 ┆ 5    ┆ 30     ┆ 14     ┆ 500000000  │
            │ 2065-01-01 10:20:30.060 ┆ 10   ┆ 20     ┆ 30     ┆ 60000000   │
            └─────────────────────────┴──────┴────────┴────────┴────────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.nanosecond())

    def ordinal_day(self: Self) -> T:
        """
        Get ordinal day.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import datetime
            >>> import narwhals as nw
            >>> data = {"a": [datetime(2020, 1, 1), datetime(2020, 8, 3)]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(a_ordinal_day=nw.col("a").dt.ordinal_day())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                       a  a_ordinal_day
            0 2020-01-01              1
            1 2020-08-03            216
            >>> func(df_pl)
            shape: (2, 2)
            ┌─────────────────────┬───────────────┐
            │ a                   ┆ a_ordinal_day │
            │ ---                 ┆ ---           │
            │ datetime[μs]        ┆ i16           │
            ╞═════════════════════╪═══════════════╡
            │ 2020-01-01 00:00:00 ┆ 1             │
            │ 2020-08-03 00:00:00 ┆ 216           │
            └─────────────────────┴───────────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.ordinal_day())

    def total_minutes(self: Self) -> T:
        """
        Get total minutes.

        Notes:
            The function outputs the total minutes in the int dtype by default,
            however, pandas may change the dtype to float when there are missing values,
            consider using `fill_null()` and `cast` in this case.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import timedelta
            >>> import narwhals as nw
            >>> data = {"a": [timedelta(minutes=10), timedelta(minutes=20, seconds=40)]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(a_total_minutes=nw.col("a").dt.total_minutes())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                            a  a_total_minutes
            0 0 days 00:10:00               10
            1 0 days 00:20:40               20
            >>> func(df_pl)
            shape: (2, 2)
            ┌──────────────┬─────────────────┐
            │ a            ┆ a_total_minutes │
            │ ---          ┆ ---             │
            │ duration[μs] ┆ i64             │
            ╞══════════════╪═════════════════╡
            │ 10m          ┆ 10              │
            │ 20m 40s      ┆ 20              │
            └──────────────┴─────────────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.total_minutes())

    def total_seconds(self: Self) -> T:
        """
        Get total seconds.

        Notes:
            The function outputs the total seconds in the int dtype by default,
            however, pandas may change the dtype to float when there are missing values,
            consider using `fill_null()` and `cast` in this case.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import timedelta
            >>> import narwhals as nw
            >>> data = {"a": [timedelta(seconds=10), timedelta(seconds=20, milliseconds=40)]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(a_total_seconds=nw.col("a").dt.total_seconds())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                                   a  a_total_seconds
            0        0 days 00:00:10               10
            1 0 days 00:00:20.040000               20
            >>> func(df_pl)
            shape: (2, 2)
            ┌──────────────┬─────────────────┐
            │ a            ┆ a_total_seconds │
            │ ---          ┆ ---             │
            │ duration[μs] ┆ i64             │
            ╞══════════════╪═════════════════╡
            │ 10s          ┆ 10              │
            │ 20s 40ms     ┆ 20              │
            └──────────────┴─────────────────┘
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).dt.total_seconds())

    def total_milliseconds(self: Self) -> T:
        """
        Get total milliseconds.

        Notes:
            The function outputs the total milliseconds in the int dtype by default,
            however, pandas may change the dtype to float when there are missing values,
            consider using `fill_null()` and `cast` in this case.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import timedelta
            >>> import narwhals as nw
            >>> data = {
            ...     "a": [
            ...         timedelta(milliseconds=10),
            ...         timedelta(milliseconds=20, microseconds=40),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         a_total_milliseconds=nw.col("a").dt.total_milliseconds()
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                                   a  a_total_milliseconds
            0 0 days 00:00:00.010000                    10
            1 0 days 00:00:00.020040                    20
            >>> func(df_pl)
            shape: (2, 2)
            ┌──────────────┬──────────────────────┐
            │ a            ┆ a_total_milliseconds │
            │ ---          ┆ ---                  │
            │ duration[μs] ┆ i64                  │
            ╞══════════════╪══════════════════════╡
            │ 10ms         ┆ 10                   │
            │ 20040µs      ┆ 20                   │
            └──────────────┴──────────────────────┘
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).dt.total_milliseconds()
        )

    def total_microseconds(self: Self) -> T:
        """
        Get total microseconds.

        Notes:
            The function outputs the total microseconds in the int dtype by default,
            however, pandas may change the dtype to float when there are missing values,
            consider using `fill_null()` and `cast` in this case.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import timedelta
            >>> import narwhals as nw
            >>> data = {
            ...     "a": [
            ...         timedelta(microseconds=10),
            ...         timedelta(milliseconds=1, microseconds=200),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         a_total_microseconds=nw.col("a").dt.total_microseconds()
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                                   a  a_total_microseconds
            0 0 days 00:00:00.000010                    10
            1 0 days 00:00:00.001200                  1200
            >>> func(df_pl)
            shape: (2, 2)
            ┌──────────────┬──────────────────────┐
            │ a            ┆ a_total_microseconds │
            │ ---          ┆ ---                  │
            │ duration[μs] ┆ i64                  │
            ╞══════════════╪══════════════════════╡
            │ 10µs         ┆ 10                   │
            │ 1200µs       ┆ 1200                 │
            └──────────────┴──────────────────────┘
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).dt.total_microseconds()
        )

    def total_nanoseconds(self: Self) -> T:
        """
        Get total nanoseconds.

        Notes:
            The function outputs the total nanoseconds in the int dtype by default,
            however, pandas may change the dtype to float when there are missing values,
            consider using `fill_null()` and `cast` in this case.

        Examples:
            >>> import pandas as pd
            >>> import polars as pl
            >>> from datetime import timedelta
            >>> import narwhals as nw
            >>> data = ["2024-01-01 00:00:00.000000001", "2024-01-01 00:00:00.000000002"]
            >>> df_pd = pd.DataFrame({"a": pd.to_datetime(data)})
            >>> df_pl = pl.DataFrame({"a": data}).with_columns(
            ...     pl.col("a").str.to_datetime(time_unit="ns")
            ... )

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         a_diff_total_nanoseconds=nw.col("a").diff().dt.total_nanoseconds()
            ...     )

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                                          a  a_diff_total_nanoseconds
            0 2024-01-01 00:00:00.000000001                       NaN
            1 2024-01-01 00:00:00.000000002                       1.0
            >>> func(df_pl)
            shape: (2, 2)
            ┌───────────────────────────────┬──────────────────────────┐
            │ a                             ┆ a_diff_total_nanoseconds │
            │ ---                           ┆ ---                      │
            │ datetime[ns]                  ┆ i64                      │
            ╞═══════════════════════════════╪══════════════════════════╡
            │ 2024-01-01 00:00:00.000000001 ┆ null                     │
            │ 2024-01-01 00:00:00.000000002 ┆ 1                        │
            └───────────────────────────────┴──────────────────────────┘
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).dt.total_nanoseconds()
        )

    def to_string(self: Self, format: str) -> T:  # noqa: A002
        """
        Convert a Date/Time/Datetime column into a String column with the given format.

        Notes:
            Unfortunately, different libraries interpret format directives a bit
            differently.

            - Chrono, the library used by Polars, uses `"%.f"` for fractional seconds,
              whereas pandas and Python stdlib use `".%f"`.
            - PyArrow interprets `"%S"` as "seconds, including fractional seconds"
              whereas most other tools interpret it as "just seconds, as 2 digits".

            Therefore, we make the following adjustments:

            - for pandas-like libraries, we replace `"%S.%f"` with `"%S%.f"`.
            - for PyArrow, we replace `"%S.%f"` with `"%S"`.

            Workarounds like these don't make us happy, and we try to avoid them as
            much as possible, but here we feel like it's the best compromise.

            If you just want to format a date/datetime Series as a local datetime
            string, and have it work as consistently as possible across libraries,
            we suggest using:

            - `"%Y-%m-%dT%H:%M:%S%.f"` for datetimes
            - `"%Y-%m-%d"` for dates

            though note that, even then, different tools may return a different number
            of trailing zeros. Nonetheless, this is probably consistent enough for
            most applications.

            If you have an application where this is not enough, please open an issue
            and let us know.

        Examples:
            >>> from datetime import datetime
            >>> import pandas as pd
            >>> import polars as pl
            >>> import narwhals as nw
            >>> data = [
            ...     datetime(2020, 3, 1),
            ...     datetime(2020, 4, 1),
            ...     datetime(2020, 5, 1),
            ... ]
            >>> df_pd = pd.DataFrame({"a": data})
            >>> df_pl = pl.DataFrame({"a": data})

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").dt.to_string("%Y/%m/%d %H:%M:%S"))

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd)
                                 a
            0  2020/03/01 00:00:00
            1  2020/04/01 00:00:00
            2  2020/05/01 00:00:00

            >>> func(df_pl)
            shape: (3, 1)
            ┌─────────────────────┐
            │ a                   │
            │ ---                 │
            │ str                 │
            ╞═════════════════════╡
            │ 2020/03/01 00:00:00 │
            │ 2020/04/01 00:00:00 │
            │ 2020/05/01 00:00:00 │
            └─────────────────────┘
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).dt.to_string(format)
        )

    def replace_time_zone(self: Self, time_zone: str | None) -> T:
        """
        Replace time zone.

        Arguments:
            time_zone: Target time zone.

        Examples:
            >>> from datetime import datetime, timezone
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {
            ...     "a": [
            ...         datetime(2024, 1, 1, tzinfo=timezone.utc),
            ...         datetime(2024, 1, 2, tzinfo=timezone.utc),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").dt.replace_time_zone("Asia/Kathmandu"))

            We can then pass pandas / PyArrow / Polars / any other supported library:

            >>> func(df_pd)
                                      a
            0 2024-01-01 00:00:00+05:45
            1 2024-01-02 00:00:00+05:45
            >>> func(df_pl)
            shape: (2, 1)
            ┌──────────────────────────────┐
            │ a                            │
            │ ---                          │
            │ datetime[μs, Asia/Kathmandu] │
            ╞══════════════════════════════╡
            │ 2024-01-01 00:00:00 +0545    │
            │ 2024-01-02 00:00:00 +0545    │
            └──────────────────────────────┘
            >>> func(df_pa)
            pyarrow.Table
            a: timestamp[us, tz=Asia/Kathmandu]
            ----
            a: [[2023-12-31 18:15:00.000000Z,2024-01-01 18:15:00.000000Z]]
        """
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).dt.replace_time_zone(time_zone)
        )

    def convert_time_zone(self: Self, time_zone: str) -> T:
        """
        Convert to a new time zone.

        If converting from a time-zone-naive column, then conversion happens
        as if converting from UTC.

        Arguments:
            time_zone: Target time zone.

        Examples:
            >>> from datetime import datetime, timezone
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {
            ...     "a": [
            ...         datetime(2024, 1, 1, tzinfo=timezone.utc),
            ...         datetime(2024, 1, 2, tzinfo=timezone.utc),
            ...     ]
            ... }
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("a").dt.convert_time_zone("Asia/Kathmandu"))

            We can then pass pandas / PyArrow / Polars / any other supported library:

            >>> func(df_pd)
                                      a
            0 2024-01-01 05:45:00+05:45
            1 2024-01-02 05:45:00+05:45
            >>> func(df_pl)
            shape: (2, 1)
            ┌──────────────────────────────┐
            │ a                            │
            │ ---                          │
            │ datetime[μs, Asia/Kathmandu] │
            ╞══════════════════════════════╡
            │ 2024-01-01 05:45:00 +0545    │
            │ 2024-01-02 05:45:00 +0545    │
            └──────────────────────────────┘
            >>> func(df_pa)
            pyarrow.Table
            a: timestamp[us, tz=Asia/Kathmandu]
            ----
            a: [[2024-01-01 00:00:00.000000Z,2024-01-02 00:00:00.000000Z]]
        """
        if time_zone is None:
            msg = "Target `time_zone` cannot be `None` in `convert_time_zone`. Please use `replace_time_zone(None)` if you want to remove the time zone."
            raise TypeError(msg)
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).dt.convert_time_zone(time_zone)
        )

    def timestamp(self: Self, time_unit: Literal["ns", "us", "ms"] = "us") -> T:
        """
        Return a timestamp in the given time unit.

        Arguments:
            time_unit: {'ns', 'us', 'ms'}
                Time unit.

        Examples:
            >>> from datetime import date
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> import pyarrow as pa
            >>> data = {"date": [date(2001, 1, 1), None, date(2001, 1, 3)]}
            >>> df_pd = pd.DataFrame(data, dtype="datetime64[ns]")
            >>> df_pl = pl.DataFrame(data)
            >>> df_pa = pa.table(data)

            Let's define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.with_columns(
            ...         nw.col("date").dt.timestamp().alias("timestamp_us"),
            ...         nw.col("date").dt.timestamp("ms").alias("timestamp_ms"),
            ...     )

            We can then pass pandas / PyArrow / Polars / any other supported library:

            >>> func(df_pd)
                    date  timestamp_us  timestamp_ms
            0 2001-01-01  9.783072e+14  9.783072e+11
            1        NaT           NaN           NaN
            2 2001-01-03  9.784800e+14  9.784800e+11
            >>> func(df_pl)
            shape: (3, 3)
            ┌────────────┬─────────────────┬──────────────┐
            │ date       ┆ timestamp_us    ┆ timestamp_ms │
            │ ---        ┆ ---             ┆ ---          │
            │ date       ┆ i64             ┆ i64          │
            ╞════════════╪═════════════════╪══════════════╡
            │ 2001-01-01 ┆ 978307200000000 ┆ 978307200000 │
            │ null       ┆ null            ┆ null         │
            │ 2001-01-03 ┆ 978480000000000 ┆ 978480000000 │
            └────────────┴─────────────────┴──────────────┘
            >>> func(df_pa)
            pyarrow.Table
            date: date32[day]
            timestamp_us: int64
            timestamp_ms: int64
            ----
            date: [[2001-01-01,null,2001-01-03]]
            timestamp_us: [[978307200000000,null,978480000000000]]
            timestamp_ms: [[978307200000,null,978480000000]]
        """
        if time_unit not in {"ns", "us", "ms"}:
            msg = (
                "invalid `time_unit`"
                f"\n\nExpected one of {{'ns', 'us', 'ms'}}, got {time_unit!r}."
            )
            raise ValueError(msg)
        return self._expr.__class__(
            lambda plx: self._expr._call(plx).dt.timestamp(time_unit)
        )


class ExprNameNamespace(Generic[T]):
    def __init__(self: Self, expr: T) -> None:
        self._expr = expr

    def keep(self: Self) -> T:
        r"""
        Keep the original root name of the expression.

        Notes:
            This will undo any previous renaming operations on the expression.
            Due to implementation constraints, this method can only be called as the last
            expression in a chain. Only one name operation per expression will work.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> data = {"foo": [1, 2], "BAR": [4, 5]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("foo").alias("alias_for_foo").name.keep())

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd).columns
            Index(['foo'], dtype='object')
            >>> func(df_pl).columns
            ['foo']
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).name.keep())

    def map(self: Self, function: Callable[[str], str]) -> T:
        r"""
        Rename the output of an expression by mapping a function over the root name.

        Arguments:
            function: Function that maps a root name to a new name.

        Notes:
            This will undo any previous renaming operations on the expression.
            Due to implementation constraints, this method can only be called as the last
            expression in a chain. Only one name operation per expression will work.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> data = {"foo": [1, 2], "BAR": [4, 5]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> renaming_func = lambda s: s[::-1]  # reverse column name
            >>> @nw.narwhalify
            ... def func(df):
            ...     return df.select(nw.col("foo", "BAR").name.map(renaming_func))

            We can then pass either pandas or Polars to `func`:

            >>> func(df_pd).columns
            Index(['oof', 'RAB'], dtype='object')
            >>> func(df_pl).columns
            ['oof', 'RAB']
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).name.map(function))

    def prefix(self: Self, prefix: str) -> T:
        r"""
        Add a prefix to the root column name of the expression.

        Arguments:
            prefix: Prefix to add to the root column name.

        Notes:
            This will undo any previous renaming operations on the expression.
            Due to implementation constraints, this method can only be called as the last
            expression in a chain. Only one name operation per expression will work.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> data = {"foo": [1, 2], "BAR": [4, 5]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def add_colname_prefix(df, prefix):
            ...     return df.select(nw.col("foo", "BAR").name.prefix(prefix))

            We can then pass either pandas or Polars to `func`:

            >>> add_colname_prefix(df_pd, "with_prefix_").columns
            Index(['with_prefix_foo', 'with_prefix_BAR'], dtype='object')

            >>> add_colname_prefix(df_pl, "with_prefix_").columns
            ['with_prefix_foo', 'with_prefix_BAR']
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).name.prefix(prefix))

    def suffix(self: Self, suffix: str) -> T:
        r"""
        Add a suffix to the root column name of the expression.

        Arguments:
            suffix: Suffix to add to the root column name.

        Notes:
            This will undo any previous renaming operations on the expression.
            Due to implementation constraints, this method can only be called as the last
            expression in a chain. Only one name operation per expression will work.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> data = {"foo": [1, 2], "BAR": [4, 5]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def add_colname_suffix(df, suffix):
            ...     return df.select(nw.col("foo", "BAR").name.suffix(suffix))

            We can then pass either pandas or Polars to `func`:

            >>> add_colname_suffix(df_pd, "_with_suffix").columns
            Index(['foo_with_suffix', 'BAR_with_suffix'], dtype='object')
            >>> add_colname_suffix(df_pl, "_with_suffix").columns
            ['foo_with_suffix', 'BAR_with_suffix']
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).name.suffix(suffix))

    def to_lowercase(self: Self) -> T:
        r"""
        Make the root column name lowercase.

        Notes:
            This will undo any previous renaming operations on the expression.
            Due to implementation constraints, this method can only be called as the last
            expression in a chain. Only one name operation per expression will work.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> data = {"foo": [1, 2], "BAR": [4, 5]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def to_lower(df):
            ...     return df.select(nw.col("foo", "BAR").name.to_lowercase())

            We can then pass either pandas or Polars to `func`:

            >>> to_lower(df_pd).columns
            Index(['foo', 'bar'], dtype='object')
            >>> to_lower(df_pl).columns
            ['foo', 'bar']
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).name.to_lowercase())

    def to_uppercase(self: Self) -> T:
        r"""
        Make the root column name uppercase.

        Notes:
            This will undo any previous renaming operations on the expression.
            Due to implementation constraints, this method can only be called as the last
            expression in a chain. Only one name operation per expression will work.

        Examples:
            >>> import narwhals as nw
            >>> import pandas as pd
            >>> import polars as pl
            >>> data = {"foo": [1, 2], "BAR": [4, 5]}
            >>> df_pd = pd.DataFrame(data)
            >>> df_pl = pl.DataFrame(data)

            We define a dataframe-agnostic function:

            >>> @nw.narwhalify
            ... def to_upper(df):
            ...     return df.select(nw.col("foo", "BAR").name.to_uppercase())

            We can then pass either pandas or Polars to `func`:
            >>> to_upper(df_pd).columns
            Index(['FOO', 'BAR'], dtype='object')
            >>> to_upper(df_pl).columns
            ['FOO', 'BAR']
        """
        return self._expr.__class__(lambda plx: self._expr._call(plx).name.to_uppercase())


def col(*names: str | Iterable[str]) -> Expr:
    """
    Creates an expression that references one or more columns by their name(s).

    Arguments:
        names: Name(s) of the columns to use in the aggregation function.

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pl = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        >>> df_pd = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        >>> df_pa = pa.table({"a": [1, 2], "b": [3, 4]})

        We define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.col("a") * nw.col("b"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
           a
        0  3
        1  8
        >>> func(df_pl)
        shape: (2, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ i64 │
        ╞═════╡
        │ 3   │
        │ 8   │
        └─────┘
        >>> func(df_pa)
        pyarrow.Table
        a: int64
        ----
        a: [[3,8]]
    """

    def func(plx: Any) -> Any:
        return plx.col(*flatten(names))

    return Expr(func)


def nth(*indices: int | Sequence[int]) -> Expr:
    """
    Creates an expression that references one or more columns by their index(es).

    Notes:
        `nth` is not supported for Polars version<1.0.0. Please use [`col`](/api-reference/narwhals/#narwhals.col) instead.

    Arguments:
        indices: One or more indices representing the columns to retrieve.

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> data = {"a": [1, 2], "b": [3, 4]}
        >>> df_pl = pl.DataFrame(data)
        >>> df_pd = pd.DataFrame(data)
        >>> df_pa = pa.table(data)

        We define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.nth(0) * 2)

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
           a
        0  2
        1  4
        >>> func(df_pl)
        shape: (2, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ i64 │
        ╞═════╡
        │ 2   │
        │ 4   │
        └─────┘
        >>> func(df_pa)
        pyarrow.Table
        a: int64
        ----
        a: [[2,4]]
    """

    def func(plx: Any) -> Any:
        return plx.nth(*flatten(indices))

    return Expr(func)


# Add underscore so it doesn't conflict with builtin `all`
def all_() -> Expr:
    """
    Instantiate an expression representing all columns.

    Examples:
        >>> import polars as pl
        >>> import pandas as pd
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pd = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        >>> df_pl = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        >>> df_pa = pa.table({"a": [1, 2, 3], "b": [4, 5, 6]})

        Let's define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.all() * 2)

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
           a   b
        0  2   8
        1  4  10
        2  6  12
        >>> func(df_pl)
        shape: (3, 2)
        ┌─────┬─────┐
        │ a   ┆ b   │
        │ --- ┆ --- │
        │ i64 ┆ i64 │
        ╞═════╪═════╡
        │ 2   ┆ 8   │
        │ 4   ┆ 10  │
        │ 6   ┆ 12  │
        └─────┴─────┘
        >>> func(df_pa)
        pyarrow.Table
        a: int64
        b: int64
        ----
        a: [[2,4,6]]
        b: [[8,10,12]]
    """
    return Expr(lambda plx: plx.all())


# Add underscore so it doesn't conflict with builtin `len`
def len_() -> Expr:
    """
    Return the number of rows.

    Examples:
        >>> import polars as pl
        >>> import pandas as pd
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pd = pd.DataFrame({"a": [1, 2], "b": [5, 10]})
        >>> df_pl = pl.DataFrame({"a": [1, 2], "b": [5, 10]})
        >>> df_pa = pa.table({"a": [1, 2], "b": [5, 10]})

        Let's define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.len())

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
           len
        0    2
        >>> func(df_pl)
        shape: (1, 1)
        ┌─────┐
        │ len │
        │ --- │
        │ u32 │
        ╞═════╡
        │ 2   │
        └─────┘
        >>> func(df_pa)
        pyarrow.Table
        len: int64
        ----
        len: [[2]]
    """

    def func(plx: Any) -> Any:
        return plx.len()

    return Expr(func)


def sum(*columns: str) -> Expr:
    """
    Sum all values.

    Note:
        Syntactic sugar for ``nw.col(columns).sum()``

    Arguments:
        columns: Name(s) of the columns to use in the aggregation function

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pl = pl.DataFrame({"a": [1, 2]})
        >>> df_pd = pd.DataFrame({"a": [1, 2]})
        >>> df_pa = pa.table({"a": [1, 2]})

        We define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.sum("a"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
           a
        0  3
        >>> func(df_pl)
        shape: (1, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ i64 │
        ╞═════╡
        │ 3   │
        └─────┘
        >>> func(df_pa)
        pyarrow.Table
        a: int64
        ----
        a: [[3]]
    """

    return Expr(lambda plx: plx.sum(*columns))


def mean(*columns: str) -> Expr:
    """
    Get the mean value.

    Note:
        Syntactic sugar for ``nw.col(columns).mean()``

    Arguments:
        columns: Name(s) of the columns to use in the aggregation function

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pl = pl.DataFrame({"a": [1, 8, 3]})
        >>> df_pd = pd.DataFrame({"a": [1, 8, 3]})
        >>> df_pa = pa.table({"a": [1, 8, 3]})

        We define a dataframe agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.mean("a"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
             a
        0  4.0
        >>> func(df_pl)
        shape: (1, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ f64 │
        ╞═════╡
        │ 4.0 │
        └─────┘
        >>> func(df_pa)
        pyarrow.Table
        a: double
        ----
        a: [[4]]
    """

    return Expr(lambda plx: plx.mean(*columns))


def median(*columns: str) -> Expr:
    """
    Get the median value.

    Notes:
        - Syntactic sugar for ``nw.col(columns).median()``
        - Results might slightly differ across backends due to differences in the underlying algorithms used to compute the median.

    Arguments:
        columns: Name(s) of the columns to use in the aggregation function

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pd = pd.DataFrame({"a": [4, 5, 2]})
        >>> df_pl = pl.DataFrame({"a": [4, 5, 2]})
        >>> df_pa = pa.table({"a": [4, 5, 2]})

        Let's define a dataframe agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.median("a"))

        We can then pass any supported library such as pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
             a
        0  4.0
        >>> func(df_pl)
        shape: (1, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ f64 │
        ╞═════╡
        │ 4.0 │
        └─────┘
        >>> func(df_pa)
        pyarrow.Table
        a: double
        ----
        a: [[4]]
    """

    return Expr(lambda plx: plx.median(*columns))


def min(*columns: str) -> Expr:
    """
    Return the minimum value.

    Note:
       Syntactic sugar for ``nw.col(columns).min()``.

    Arguments:
        columns: Name(s) of the columns to use in the aggregation function.

    Examples:
        >>> import polars as pl
        >>> import pandas as pd
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pd = pd.DataFrame({"a": [1, 2], "b": [5, 10]})
        >>> df_pl = pl.DataFrame({"a": [1, 2], "b": [5, 10]})
        >>> df_pa = pa.table({"a": [1, 2], "b": [5, 10]})

        Let's define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.min("b"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
           b
        0  5
        >>> func(df_pl)
        shape: (1, 1)
        ┌─────┐
        │ b   │
        │ --- │
        │ i64 │
        ╞═════╡
        │ 5   │
        └─────┘
        >>> func(df_pa)
        pyarrow.Table
        b: int64
        ----
        b: [[5]]
    """
    return Expr(lambda plx: plx.min(*columns))


def max(*columns: str) -> Expr:
    """
    Return the maximum value.

    Note:
       Syntactic sugar for ``nw.col(columns).max()``.

    Arguments:
        columns: Name(s) of the columns to use in the aggregation function.

    Examples:
        >>> import polars as pl
        >>> import pandas as pd
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pd = pd.DataFrame({"a": [1, 2], "b": [5, 10]})
        >>> df_pl = pl.DataFrame({"a": [1, 2], "b": [5, 10]})
        >>> df_pa = pa.table({"a": [1, 2], "b": [5, 10]})

        Let's define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.max("a"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
           a
        0  2
        >>> func(df_pl)
        shape: (1, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ i64 │
        ╞═════╡
        │ 2   │
        └─────┘
        >>> func(df_pa)
        pyarrow.Table
        a: int64
        ----
        a: [[2]]
    """
    return Expr(lambda plx: plx.max(*columns))


def sum_horizontal(*exprs: IntoExpr | Iterable[IntoExpr]) -> Expr:
    """
    Sum all values horizontally across columns.

    Warning:
        Unlike Polars, we support horizontal sum over numeric columns only.

    Arguments:
        exprs: Name(s) of the columns to use in the aggregation function. Accepts
            expression input.

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> data = {"a": [1, 2, 3], "b": [5, 10, None]}
        >>> df_pl = pl.DataFrame(data)
        >>> df_pd = pd.DataFrame(data)
        >>> df_pa = pa.table(data)

        We define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.sum_horizontal("a", "b"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
              a
        0   6.0
        1  12.0
        2   3.0
        >>> func(df_pl)
        shape: (3, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ i64 │
        ╞═════╡
        │ 6   │
        │ 12  │
        │ 3   │
        └─────┘
        >>> func(df_pa)
        pyarrow.Table
        a: int64
        ----
        a: [[6,12,3]]
    """
    if not exprs:
        msg = "At least one expression must be passed to `sum_horizontal`"
        raise ValueError(msg)
    return Expr(
        lambda plx: plx.sum_horizontal(
            *[extract_compliant(plx, v) for v in flatten(exprs)]
        )
    )


def min_horizontal(*exprs: IntoExpr | Iterable[IntoExpr]) -> Expr:
    """
    Get the minimum value horizontally across columns.

    Notes:
        We support `min_horizontal` over numeric columns only.

    Arguments:
        exprs: Name(s) of the columns to use in the aggregation function. Accepts
            expression input.

    Examples:
        >>> import narwhals as nw
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> data = {
        ...     "a": [1, 8, 3],
        ...     "b": [4, 5, None],
        ...     "c": ["x", "y", "z"],
        ... }

        We define a dataframe-agnostic function that computes the horizontal min of "a"
        and "b" columns:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.min_horizontal("a", "b"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(pd.DataFrame(data))
             a
        0  1.0
        1  5.0
        2  3.0
        >>> func(pl.DataFrame(data))
        shape: (3, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ i64 │
        ╞═════╡
        │ 1   │
        │ 5   │
        │ 3   │
        └─────┘
        >>> func(pa.table(data))
        pyarrow.Table
        a: int64
        ----
        a: [[1,5,3]]
    """
    if not exprs:
        msg = "At least one expression must be passed to `min_horizontal`"
        raise ValueError(msg)
    return Expr(
        lambda plx: plx.min_horizontal(
            *[extract_compliant(plx, v) for v in flatten(exprs)]
        )
    )


def max_horizontal(*exprs: IntoExpr | Iterable[IntoExpr]) -> Expr:
    """
    Get the maximum value horizontally across columns.

    Notes:
        We support `max_horizontal` over numeric columns only.

    Arguments:
        exprs: Name(s) of the columns to use in the aggregation function. Accepts
            expression input.

    Examples:
        >>> import narwhals as nw
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> data = {
        ...     "a": [1, 8, 3],
        ...     "b": [4, 5, None],
        ...     "c": ["x", "y", "z"],
        ... }

        We define a dataframe-agnostic function that computes the horizontal max of "a"
        and "b" columns:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.max_horizontal("a", "b"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(pd.DataFrame(data))
             a
        0  4.0
        1  8.0
        2  3.0
        >>> func(pl.DataFrame(data))
        shape: (3, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ i64 │
        ╞═════╡
        │ 4   │
        │ 8   │
        │ 3   │
        └─────┘
        >>> func(pa.table(data))
        pyarrow.Table
        a: int64
        ----
        a: [[4,8,3]]
    """
    if not exprs:
        msg = "At least one expression must be passed to `max_horizontal`"
        raise ValueError(msg)
    return Expr(
        lambda plx: plx.max_horizontal(
            *[extract_compliant(plx, v) for v in flatten(exprs)]
        )
    )


class When:
    def __init__(self, *predicates: IntoExpr | Iterable[IntoExpr]) -> None:
        self._predicates = flatten([predicates])

    def _extract_predicates(self, plx: Any) -> Any:
        return [extract_compliant(plx, v) for v in self._predicates]

    def then(self, value: Any) -> Then:
        return Then(
            lambda plx: plx.when(*self._extract_predicates(plx)).then(
                extract_compliant(plx, value)
            )
        )


class Then(Expr):
    def __init__(self, call: Callable[[Any], Any]) -> None:
        self._call = call

    def otherwise(self, value: Any) -> Expr:
        return Expr(lambda plx: self._call(plx).otherwise(extract_compliant(plx, value)))


def when(*predicates: IntoExpr | Iterable[IntoExpr]) -> When:
    """
    Start a `when-then-otherwise` expression.

    Expression similar to an `if-else` statement in Python. Always initiated by a `pl.when(<condition>).then(<value if condition>)`., and optionally followed by chaining one or more `.when(<condition>).then(<value>)` statements.
    Chained when-then operations should be read as Python `if, elif, ... elif` blocks, not as `if, if, ... if`, i.e. the first condition that evaluates to `True` will be picked.
    If none of the conditions are `True`, an optional `.otherwise(<value if all statements are false>)` can be appended at the end. If not appended, and none of the conditions are `True`, `None` will be returned.

    Arguments:
        predicates: Condition(s) that must be met in order to apply the subsequent statement. Accepts one or more boolean expressions, which are implicitly combined with `&`. String input is parsed as a column name.

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pl = pl.DataFrame({"a": [1, 2, 3], "b": [5, 10, 15]})
        >>> df_pd = pd.DataFrame({"a": [1, 2, 3], "b": [5, 10, 15]})
        >>> df_pa = pa.table({"a": [1, 2, 3], "b": [5, 10, 15]})

        We define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df_any):
        ...     return df_any.with_columns(
        ...         nw.when(nw.col("a") < 3).then(5).otherwise(6).alias("a_when")
        ...     )

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
           a   b  a_when
        0  1   5       5
        1  2  10       5
        2  3  15       6
        >>> func(df_pl)
        shape: (3, 3)
        ┌─────┬─────┬────────┐
        │ a   ┆ b   ┆ a_when │
        │ --- ┆ --- ┆ ---    │
        │ i64 ┆ i64 ┆ i32    │
        ╞═════╪═════╪════════╡
        │ 1   ┆ 5   ┆ 5      │
        │ 2   ┆ 10  ┆ 5      │
        │ 3   ┆ 15  ┆ 6      │
        └─────┴─────┴────────┘
        >>> func(df_pa)
        pyarrow.Table
        a: int64
        b: int64
        a_when: int64
        ----
        a: [[1,2,3]]
        b: [[5,10,15]]
        a_when: [[5,5,6]]
    """
    return When(*predicates)


def all_horizontal(*exprs: IntoExpr | Iterable[IntoExpr]) -> Expr:
    r"""
    Compute the bitwise AND horizontally across columns.

    Arguments:
        exprs: Name(s) of the columns to use in the aggregation function. Accepts expression input.

    Notes:
        pandas and Polars handle null values differently.

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> data = {
        ...     "a": [False, False, True, True, False, None],
        ...     "b": [False, True, True, None, None, None],
        ... }
        >>> df_pl = pl.DataFrame(data)
        >>> df_pd = pd.DataFrame(data)
        >>> df_pa = pa.table(data)

        We define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select("a", "b", all=nw.all_horizontal("a", "b"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
               a      b    all
        0  False  False  False
        1  False   True  False
        2   True   True   True
        3   True   None  False
        4  False   None  False
        5   None   None  False

        >>> func(df_pl)
        shape: (6, 3)
        ┌───────┬───────┬───────┐
        │ a     ┆ b     ┆ all   │
        │ ---   ┆ ---   ┆ ---   │
        │ bool  ┆ bool  ┆ bool  │
        ╞═══════╪═══════╪═══════╡
        │ false ┆ false ┆ false │
        │ false ┆ true  ┆ false │
        │ true  ┆ true  ┆ true  │
        │ true  ┆ null  ┆ null  │
        │ false ┆ null  ┆ false │
        │ null  ┆ null  ┆ null  │
        └───────┴───────┴───────┘

        >>> func(df_pa)
        pyarrow.Table
        a: bool
        b: bool
        all: bool
        ----
        a: [[false,false,true,true,false,null]]
        b: [[false,true,true,null,null,null]]
        all: [[false,false,true,null,false,null]]
    """
    if not exprs:
        msg = "At least one expression must be passed to `all_horizontal`"
        raise ValueError(msg)
    return Expr(
        lambda plx: plx.all_horizontal(
            *[extract_compliant(plx, v) for v in flatten(exprs)]
        )
    )


def lit(value: Any, dtype: DType | None = None) -> Expr:
    """
    Return an expression representing a literal value.

    Arguments:
        value: The value to use as literal.
        dtype: The data type of the literal value. If not provided, the data type will be inferred.

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> df_pl = pl.DataFrame({"a": [1, 2]})
        >>> df_pd = pd.DataFrame({"a": [1, 2]})
        >>> df_pa = pa.table({"a": [1, 2]})

        We define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.with_columns(nw.lit(3))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
           a  literal
        0  1        3
        1  2        3
        >>> func(df_pl)
        shape: (2, 2)
        ┌─────┬─────────┐
        │ a   ┆ literal │
        │ --- ┆ ---     │
        │ i64 ┆ i32     │
        ╞═════╪═════════╡
        │ 1   ┆ 3       │
        │ 2   ┆ 3       │
        └─────┴─────────┘
        >>> func(df_pa)
        pyarrow.Table
        a: int64
        literal: int64
        ----
        a: [[1,2]]
        literal: [[3,3]]
    """
    if is_numpy_array(value):
        msg = (
            "numpy arrays are not supported as literal values. "
            "Consider using `with_columns` to create a new column from the array."
        )
        raise ValueError(msg)

    if isinstance(value, (list, tuple)):
        msg = f"Nested datatypes are not supported yet. Got {value}"
        raise NotImplementedError(msg)

    return Expr(lambda plx: plx.lit(value, dtype))


def any_horizontal(*exprs: IntoExpr | Iterable[IntoExpr]) -> Expr:
    r"""
    Compute the bitwise OR horizontally across columns.

    Arguments:
        exprs: Name(s) of the columns to use in the aggregation function. Accepts expression input.

    Notes:
        pandas and Polars handle null values differently.

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> data = {
        ...     "a": [False, False, True, True, False, None],
        ...     "b": [False, True, True, None, None, None],
        ... }
        >>> df_pl = pl.DataFrame(data)
        >>> df_pd = pd.DataFrame(data)
        >>> df_pa = pa.table(data)

        We define a dataframe-agnostic function:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select("a", "b", any=nw.any_horizontal("a", "b"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
               a      b    any
        0  False  False  False
        1  False   True   True
        2   True   True   True
        3   True   None   True
        4  False   None  False
        5   None   None  False

        >>> func(df_pl)
        shape: (6, 3)
        ┌───────┬───────┬───────┐
        │ a     ┆ b     ┆ any   │
        │ ---   ┆ ---   ┆ ---   │
        │ bool  ┆ bool  ┆ bool  │
        ╞═══════╪═══════╪═══════╡
        │ false ┆ false ┆ false │
        │ false ┆ true  ┆ true  │
        │ true  ┆ true  ┆ true  │
        │ true  ┆ null  ┆ true  │
        │ false ┆ null  ┆ null  │
        │ null  ┆ null  ┆ null  │
        └───────┴───────┴───────┘

        >>> func(df_pa)
        pyarrow.Table
        a: bool
        b: bool
        any: bool
        ----
        a: [[false,false,true,true,false,null]]
        b: [[false,true,true,null,null,null]]
        any: [[false,true,true,true,null,null]]
    """
    if not exprs:
        msg = "At least one expression must be passed to `any_horizontal`"
        raise ValueError(msg)
    return Expr(
        lambda plx: plx.any_horizontal(
            *[extract_compliant(plx, v) for v in flatten(exprs)]
        )
    )


def mean_horizontal(*exprs: IntoExpr | Iterable[IntoExpr]) -> Expr:
    """
    Compute the mean of all values horizontally across columns.

    Arguments:
        exprs: Name(s) of the columns to use in the aggregation function. Accepts
            expression input.

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> import narwhals as nw
        >>> data = {
        ...     "a": [1, 8, 3],
        ...     "b": [4, 5, None],
        ...     "c": ["x", "y", "z"],
        ... }
        >>> df_pl = pl.DataFrame(data)
        >>> df_pd = pd.DataFrame(data)
        >>> df_pa = pa.table(data)

        We define a dataframe-agnostic function that computes the horizontal mean of "a"
        and "b" columns:

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(nw.mean_horizontal("a", "b"))

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(df_pd)
             a
        0  2.5
        1  6.5
        2  3.0

        >>> func(df_pl)
        shape: (3, 1)
        ┌─────┐
        │ a   │
        │ --- │
        │ f64 │
        ╞═════╡
        │ 2.5 │
        │ 6.5 │
        │ 3.0 │
        └─────┘

        >>> func(df_pa)
        pyarrow.Table
        a: double
        ----
        a: [[2.5,6.5,3]]
    """
    if not exprs:
        msg = "At least one expression must be passed to `mean_horizontal`"
        raise ValueError(msg)
    return Expr(
        lambda plx: plx.mean_horizontal(
            *[extract_compliant(plx, v) for v in flatten(exprs)]
        )
    )


def concat_str(
    exprs: IntoExpr | Iterable[IntoExpr],
    *more_exprs: IntoExpr,
    separator: str = "",
    ignore_nulls: bool = False,
) -> Expr:
    r"""
    Horizontally concatenate columns into a single string column.

    Arguments:
        exprs: Columns to concatenate into a single string column. Accepts expression
            input. Strings are parsed as column names, other non-expression inputs are
            parsed as literals. Non-`String` columns are cast to `String`.
        *more_exprs: Additional columns to concatenate into a single string column,
            specified as positional arguments.
        separator: String that will be used to separate the values of each column.
        ignore_nulls: Ignore null values (default is `False`).
            If set to `False`, null values will be propagated and if the row contains any
            null values, the output is null.

    Examples:
        >>> import narwhals as nw
        >>> import pandas as pd
        >>> import polars as pl
        >>> import pyarrow as pa
        >>> data = {
        ...     "a": [1, 2, 3],
        ...     "b": ["dogs", "cats", None],
        ...     "c": ["play", "swim", "walk"],
        ... }

        We define a dataframe-agnostic function that computes the horizontal string
        concatenation of different columns

        >>> @nw.narwhalify
        ... def func(df):
        ...     return df.select(
        ...         nw.concat_str(
        ...             [
        ...                 nw.col("a") * 2,
        ...                 nw.col("b"),
        ...                 nw.col("c"),
        ...             ],
        ...             separator=" ",
        ...         ).alias("full_sentence")
        ...     )

        We can pass any supported library such as Pandas, Polars, or PyArrow to `func`:

        >>> func(pd.DataFrame(data))
          full_sentence
        0   2 dogs play
        1   4 cats swim
        2          None

        >>> func(pl.DataFrame(data))
        shape: (3, 1)
        ┌───────────────┐
        │ full_sentence │
        │ ---           │
        │ str           │
        ╞═══════════════╡
        │ 2 dogs play   │
        │ 4 cats swim   │
        │ null          │
        └───────────────┘

        >>> func(pa.table(data))
        pyarrow.Table
        full_sentence: string
        ----
        full_sentence: [["2 dogs play","4 cats swim",null]]
    """
    return Expr(
        lambda plx: plx.concat_str(
            [extract_compliant(plx, v) for v in flatten([exprs])],
            *[extract_compliant(plx, v) for v in more_exprs],
            separator=separator,
            ignore_nulls=ignore_nulls,
        )
    )


__all__ = [
    "Expr",
]