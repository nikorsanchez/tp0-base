package protocol

const (
    HeaderTypeBet      = 0x01
    HeaderTypeConfirm  = 0x02
	HeaderTypeFailure  = 0x03
    HeaderSize         = 3 // 2 bytes length + 1 byte type
    MaxMessageSize     = 0xFFFF // Max 65535 bytes
    FieldSeparator     = '|'
    FieldEndMarker     = '\n'
)