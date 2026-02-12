ml.onStart(ml.event.None, function () {
  radio.sendString("none");
});
ml.onStart(ml.event.B, function () {
  radio.sendString("l");
});
ml.onStart(ml.event.Left, function () {
  radio.sendString("h");
});
ml.onStart(ml.event.A, function () {
  radio.sendString("m");
});
ml.onStart(ml.event.Hadouken, function () {
  radio.sendString("hadouken");
});
ml.onStart(ml.event.Unknown, function () {
  radio.sendString("none");
});
ml.onStart(ml.event.Down, function () {
  radio.sendString("j");
});
ml.onStart(ml.event.Right, function () {
  radio.sendString("k");
});
ml.onStart(ml.event.Up, function () {
  radio.sendString("u");
});
radio.setGroup(1);
radio.setTransmitSerialNumber(true);
basic.showNumber(2);
