type Atome = str | int | float | bool | list[Serializable] | list[Atome] | None
type Serializable = dict[str, Serializable] | Atome
