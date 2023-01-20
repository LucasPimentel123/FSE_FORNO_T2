constant = bytes([6,6,6,3])

request_internal_temp = b'\x01\x23\xc1' + constant + b''

request_ref_temp = b'\x01\x23\xc2' + constant + b''

read_user_commands = b'\x01\x23\xc3' + constant + b''

send_control_signal= b'\x01\x23\xd1' + constant

send_ref_signal ={"message": b'\x01\x23\xd2' + constant}

send_sys_on_off =  b'\x01\x23\xd3' + constant

change_ref_temp_control_mode =  b'\x01\x23\xd4' + constant

send_sys_state = b'\x01\x23\xd5' + constant

send_room_temp = b'\x01\x23\xd6' + constant

