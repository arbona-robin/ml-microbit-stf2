// MakeCode (micro:bit récepteur) — détecte P1/P2 par serial number
// et envoie "P1:commande" ou "P2:commande" via USB série
//
// PROBLÈME RÉSOLU : sans le flag `writing`, le callback radio tire plus
// vite que serial.writeLine ne peut écrire (~20-64 octets de buffer TX).
// Résultat : lignes fusionnées ("P1:x\rP1:z") et troncatures.
// FIX : on ignore les messages radio reçus pendant une écriture série.

let players: { [key: number]: number } = {}
let playerCount = 0
let writing = false

radio.onReceivedString(function (receivedString) {
    if (writing) return   // évite le débordement du buffer TX série
    let sn = radio.receivedPacket(RadioPacketProperty.SerialNumber)
    if (!players[sn]) {
        if (playerCount >= 2) return
        playerCount += 1
        players[sn] = playerCount
    }
    writing = true
    serial.writeLine("P" + players[sn] + ":" + receivedString)
    writing = false
})

radio.setGroup(1)
radio.setTransmitPower(7)
basic.showLeds(`
    . . . . .
    . # . # .
    . . . . .
    # . . . #
    . # # # .
    `)
