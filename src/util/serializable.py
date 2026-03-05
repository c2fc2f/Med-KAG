type Atome = str | int | float | bool | list[Serializable] | None
type Serializable = dict[str, Serializable] | Atome
