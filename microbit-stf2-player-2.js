ml.onStart(ml.event.None, function () {
  radio.sendString("0");
});
ml.onStart(ml.event.B, function () {
  radio.sendString("l");
});
ml.onStart(ml.event.Left, function () {
  radio.sendString("1");
});
ml.onStart(ml.event.A, function () {
  radio.sendString("m");
});
ml.onStart(ml.event.Hadouken, function () {
  radio.sendString("!");
});
ml.onStart(ml.event.Unknown, function () {
  radio.sendString("0");
});
ml.onStart(ml.event.Down, function () {
  radio.sendString("4");
});
ml.onStart(ml.event.Right, function () {
  radio.sendString("2");
});
ml.onStart(ml.event.Up, function () {
  radio.sendString("3");
});
radio.setGroup(1);
radio.setTransmitSerialNumber(true);
basic.showNumber(2);
