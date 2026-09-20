from .config import DATA_LEN_CHARS, TOTAL_EXPECTED_BITS
from .dsp import hamming_74_decode, hamming_74_encode


class ChirpProtocol:
    @staticmethod
    def _crc8(data_bits):
        """CRC-8 (polynomial 0x07, init 0x00) over a bit string, MSB first."""
        crc = 0
        for bit in data_bits:
            if ((crc >> 7) & 1) ^ int(bit):
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
        return format(crc, "08b")

    @staticmethod
    def encode_to_bits(text):
        """编码文本为位流"""
        text = text[:DATA_LEN_CHARS].ljust(DATA_LEN_CHARS, " ")

        # 1. 原始数据位
        raw_bits = ""
        for char in text:
            raw_bits += format(ord(char), "08b")

        # 2. 用 Hamming(7,4) 编码每个 nibble
        encoded = ""
        for i in range(0, len(raw_bits), 4):
            nibble = raw_bits[i : i + 4]
            if len(nibble) == 4:
                encoded += hamming_74_encode(nibble)

        # 3. 添加奇偶校验位（每 7 位添加 1 位奇偶校验）
        encoded_with_parity = ""
        for i in range(0, len(encoded), 7):
            block = encoded[i : i + 7]
            if len(block) == 7:
                parity = str(sum(int(b) for b in block) % 2)
                encoded_with_parity += block + parity

        # 4. 计算并编码 CRC-8
        crc = ChirpProtocol._crc8(raw_bits)
        crc_encoded = hamming_74_encode(crc[:4]) + hamming_74_encode(crc[4:])

        return encoded_with_parity + crc_encoded

    @staticmethod
    def decode_from_bits(bit_stream):
        """解码位流为文本"""
        if len(bit_stream) < TOTAL_EXPECTED_BITS:
            return "???"

        # 分离数据位和 CRC 位
        data_encoded = bit_stream[:-14]
        crc_encoded = bit_stream[-14:]

        # Remove the per-block parity bit and Hamming-decode. The parity bit is
        # kept for framing compatibility; Hamming(7,4) already corrects a
        # single-bit error per codeword and the trailing CRC guards the frame.
        raw_bits = ""
        i = 0
        while i < len(data_encoded):
            if i + 8 <= len(data_encoded):
                block = data_encoded[i : i + 7]
                raw_bits += hamming_74_decode(block)
            i += 8

        # 解码 CRC
        crc_decoded = hamming_74_decode(crc_encoded[:7]) + hamming_74_decode(crc_encoded[7:14])

        # 计算 CRC 并验证
        calculated_crc = ChirpProtocol._crc8(raw_bits)
        if crc_decoded != calculated_crc:
            return "!!!"

        # 转换为字符
        chars = []
        for i in range(0, len(raw_bits), 8):
            byte_bits = raw_bits[i : i + 8]
            if len(byte_bits) == 8:
                byte_val = int(byte_bits, 2)
                if 32 <= byte_val <= 126:
                    chars.append(chr(byte_val))
                else:
                    chars.append("?")
        return "".join(chars)
