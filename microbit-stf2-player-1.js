ml.onStart(ml.event.None, function () {
  radio.sendString("none");
});
ml.onStart(ml.event.B, function () {
  radio.sendString("x");
});
ml.onStart(ml.event.Left, function () {
  radio.sendString("left");
});
ml.onStart(ml.event.A, function () {
  radio.sendString("z");
});
ml.onStart(ml.event.Hadouken, function () {
  radio.sendString("hadouken");
});
ml.onStart(ml.event.Unknown, function () {
  radio.sendString("none");
});
ml.onStart(ml.event.Down, function () {
  radio.sendString("down");
});
ml.onStart(ml.event.Right, function () {
  radio.sendString("right");
});
ml.onStart(ml.event.Up, function () {
  radio.sendString("up");
});
radio.setGroup(1);
radio.setTransmitSerialNumber(true);
basic.showNumber(1);
