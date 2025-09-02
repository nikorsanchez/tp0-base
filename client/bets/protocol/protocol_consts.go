package protocol

const (
	HeaderTypeBetBatch     = 0x01
	HeaderTypeConfirm      = 0x02
	HeaderTypeFailure      = 0x03
	HeaderTypeFinishNotify = 0x04
	HeaderTypeWinnersQuery = 0x05
	HeaderTypeWinnersList  = 0x06
	HeaderSize             = 3      // 2 bytes length + 1 byte type
	MaxMessageSize         = 0xFFFF // Max 65535 bytes
	FieldSeparator         = '|'
	BetSeparator           = ';'
	FieldEndMarker         = '\n'
	EmptySizeBody          = 0
)
