(module
  (func (export "govern") (param i32 i32 i32 i32 i32 i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.and
    local.get 2
    i32.and
    local.get 3
    i32.and
    local.get 4
    i32.and
    local.get 5
    i32.and
    local.get 6
    i32.and
  )
)