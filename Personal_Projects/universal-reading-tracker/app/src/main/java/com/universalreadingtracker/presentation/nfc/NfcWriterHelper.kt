package com.universalreadingtracker.presentation.nfc

import android.nfc.NdefMessage
import android.nfc.NdefRecord
import android.nfc.Tag
import android.nfc.tech.Ndef
import android.nfc.tech.NdefFormatable
import java.io.IOException

/**
 * Utility to write the Kindle trigger URI ("readingtracker://kindle") to an NFC sticker (NTAG213/215/216).
 * Implements RF-11 from spec.md.
 */
object NfcWriterHelper {

    const val KINDLE_TRIGGER_URI = "readingtracker://kindle"

    fun writeKindleTag(tag: Tag): Result<Unit> {
        val uriRecord = NdefRecord.createUri(KINDLE_TRIGGER_URI)
        val ndefMessage = NdefMessage(arrayOf(uriRecord))

        val ndef = Ndef.get(tag)
        return try {
            if (ndef != null) {
                ndef.connect()
                if (!ndef.isWritable) {
                    return Result.failure(IllegalStateException("El sticker NFC está bloqueado o es de solo lectura."))
                }
                if (ndef.maxSize < ndefMessage.toByteArray().size) {
                    return Result.failure(IllegalStateException("El sticker NFC no tiene suficiente capacidad."))
                }
                ndef.writeNdefMessage(ndefMessage)
                ndef.close()
                Result.success(Unit)
            } else {
                val formatable = NdefFormatable.get(tag)
                if (formatable != null) {
                    formatable.connect()
                    formatable.format(ndefMessage)
                    formatable.close()
                    Result.success(Unit)
                } else {
                    Result.failure(IllegalArgumentException("El tag no soporta formato NDEF."))
                }
            }
        } catch (e: IOException) {
            Result.failure(e)
        }
    }
}
