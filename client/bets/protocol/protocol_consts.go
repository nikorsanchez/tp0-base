package protocol

const (
    HeaderTypeBet      = 1
    HeaderTypeConfirm  = 2
    HeaderSize         = 1
    LengthSize         = 3
    FullHeaderSize     = HeaderSize + LengthSize
)