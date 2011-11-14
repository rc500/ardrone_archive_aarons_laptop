import json, logging, os, sys

import ardrone.util.qtcompat as qt

QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')
QtGui = qt.import_module('QtGui')

RIGHT = 0
DOWN = 1
LEFT = 2
UP = 3

CONTROL_SCALE = 0.3 # How much to change each control value by when button is pressed.

class Application(QtGui.QApplication):
  def __init__(self, *args, **kwargs):
    super(Application, self).__init__(sys.argv, *args, **kwargs)

class ControllerWindow(QtGui.QWidget):
  def __init__(self, host='127.0.0.1', port=5560, *args, **kwargs):
    super(ControllerWindow, self).__init__(*args, **kwargs)

    self.setWindowTitle('Drone controller')
    self._control_state = {
        'roll': 0.0,
        'pitch': 0.0,
        'yaw': 0.0,
        'gas': 0.0,
        'take_off': False,
        'reset': False,
        'hover': False,
        }
    self._key_state = {
        'W': False,
        'A': False,
        'S': False,
        'D': False,
        'Up': False,
        'Down': False,
        'Left': False,
        'Right': False,
        }
    self.setMinimumSize(self.sizeHint())

    self._auto_hover_timer = QtCore.QTimer()
    self._auto_hover_timer.setSingleShot(True)
    self._auto_hover_timer.setInterval(100) # milliseconds
    self._auto_hover_timer.timeout.connect(self._set_auto_hover)

    self._control_socket = QtNetwork.QUdpSocket()
    self._control_host = QtNetwork.QHostAddress(host)
    self._control_port = port

    # This is a timer that sends a control sequence every so often come what
    # may.
    self._control_timer = QtCore.QTimer()
    self._control_timer.setInterval(250) # milliseconds
    self._control_timer.timeout.connect(self._send_state)
    self._control_timer.start()
    self._seq = 0

    self._new_state()

  def sizeHint(self):
    return QtCore.QSize(550,200)

  def _send_state(self):
    self._seq += 1
    packet = json.dumps({'seq': self._seq, 'state': self._control_state})
    if -1 == self._control_socket.writeDatagram(packet, self._control_host, self._control_port):
      logging.error('Failed to send to %s:%s. Error was: %s' %
          (self._control_host.toString(), self._control_port, self._control_socket.errorString()))
      raise base.ConnectionError(self._control_socket.errorString())

  def _should_auto_hover(self):
    return [self._control_state[x] for x in ('roll', 'pitch', 'yaw', 'gas')] == [0.0,0.0,0.0,0.0]

  def _set_auto_hover(self):
    self._control_state['hover'] = self._should_auto_hover()
    self.update()

  def _new_state(self):
    sah = self._should_auto_hover()
    ah_timer_active = self._auto_hover_timer.isActive()

    if sah and not ah_timer_active:
      self._auto_hover_timer.start()

    if not sah:
      self._auto_hover_timer.stop()
      self._control_state['hover'] = False

    self._send_state()
    self.update()

  def keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_A:
      self._control_state['roll'] -= CONTROL_SCALE
      self._key_state['A'] = True
    elif event.key() == QtCore.Qt.Key_D:
      self._control_state['roll'] += CONTROL_SCALE
      self._key_state['D'] = True
    elif event.key() == QtCore.Qt.Key_S:
      self._control_state['pitch'] += CONTROL_SCALE
      self._key_state['S'] = True
    elif event.key() == QtCore.Qt.Key_W:
      self._control_state['pitch'] -= CONTROL_SCALE
      self._key_state['W'] = True
    elif event.key() == QtCore.Qt.Key_Left:
      self._control_state['yaw'] -= CONTROL_SCALE
      self._key_state['Left'] = True
    elif event.key() == QtCore.Qt.Key_Right:
      self._control_state['yaw'] += CONTROL_SCALE
      self._key_state['Right'] = True
    elif event.key() == QtCore.Qt.Key_Down:
      self._control_state['gas'] -= CONTROL_SCALE
      self._key_state['Down'] = True
    elif event.key() == QtCore.Qt.Key_Up:
      self._control_state['gas'] += CONTROL_SCALE
      self._key_state['Up'] = True
    elif event.key() == QtCore.Qt.Key_T:
      self._control_state['take_off'] = True
    elif event.key() == QtCore.Qt.Key_R:
      self._control_state['reset'] = True
    else:
      return

    self._new_state()

  def keyReleaseEvent(self, event):
    if event.key() == QtCore.Qt.Key_A:
      self._control_state['roll'] += CONTROL_SCALE
      self._key_state['A'] = False
    elif event.key() == QtCore.Qt.Key_D:
      self._control_state['roll'] -= CONTROL_SCALE
      self._key_state['D'] = False
    elif event.key() == QtCore.Qt.Key_S:
      self._control_state['pitch'] -= CONTROL_SCALE
      self._key_state['S'] = False
    elif event.key() == QtCore.Qt.Key_W:
      self._control_state['pitch'] += CONTROL_SCALE
      self._key_state['W'] = False
    elif event.key() == QtCore.Qt.Key_Left:
      self._control_state['yaw'] += CONTROL_SCALE
      self._key_state['Left'] = False
    elif event.key() == QtCore.Qt.Key_Right:
      self._control_state['yaw'] -= CONTROL_SCALE
      self._key_state['Right'] = False
    elif event.key() == QtCore.Qt.Key_Down:
      self._control_state['gas'] += CONTROL_SCALE
      self._key_state['Down'] = False
    elif event.key() == QtCore.Qt.Key_Up:
      self._control_state['gas'] -= CONTROL_SCALE
      self._key_state['Up'] = False
    elif event.key() == QtCore.Qt.Key_T:
      self._control_state['take_off'] = False
    elif event.key() == QtCore.Qt.Key_R:
      self._control_state['reset'] = False
    else:
      return

    self._new_state()

  def paintEvent(self, event):
    painter = QtGui.QPainter(self)

    mid_x = self.width() / 2.0
    mid_y = self.height() / 2.0

    pad_size = min(self.height(), 60)
    pad_separation = pad_size
    mid_x -= 1.5*pad_size
    mid_y += 0.2*pad_size

    painter.save()
    painter.setTransform(QtGui.QTransform.fromTranslate(mid_x - pad_size - 0.5*pad_separation, mid_y))
    self._draw_pad(painter, ('A', 'D', 'W', 'S'), 'Roll/pitch:\n{A,D}/{W,S}', pad_size)
    painter.restore()

    painter.save()
    painter.setTransform(QtGui.QTransform.fromTranslate(mid_x + pad_size + 0.5*pad_separation, mid_y))

    # magic to support Python2 and 3
    try:
      chars = tuple(unichr(x) for x in (0x2190, 0x2192, 0x2191, 0x2193))
    except NameError:
      chars = ('\u2190', '\u2192', '\u2191', '\u2193')

    self._draw_pad(painter, ('Left', 'Right', 'Up', 'Down'), 'Yaw/gas:\n{%s,%s}/{%s,%s}' % chars, pad_size)
    painter.restore()

    mid_y -= 0.2*pad_size
    
    painter.save()
    painter.setTransform(QtGui.QTransform.fromTranslate(self.width() - 3*pad_size,mid_y-pad_size))
    self._draw_led(painter, 'Take off/land (T)', self._control_state['take_off'])
    painter.restore()
    
    painter.save()
    painter.setTransform(QtGui.QTransform.fromTranslate(self.width() - 3*pad_size,mid_y-0.5*pad_size))
    self._draw_led(painter, 'Reset/emergency (R)', self._control_state['reset'])
    painter.restore()
    
    painter.save()
    painter.setTransform(QtGui.QTransform.fromTranslate(self.width() - 3*pad_size,mid_y))
    self._draw_led(painter, 'Auto-hover', self._control_state['hover'])
    painter.restore()

  def _draw_led(self, painter, label, state):
    glow_brush = QtGui.QBrush(QtCore.Qt.red)
    dark_brush = QtGui.QBrush(QtCore.Qt.lightGray)

    fm = painter.fontMetrics()
    th = fm.height()

    if state:
      painter.setBrush(glow_brush)
    else:
      painter.setBrush(dark_brush)
    painter.drawEllipse(0,0,0.5*th,0.5*th)
    painter.drawText(th,0.5*th,label)

  def _draw_pad(self, painter, key_state, label, pad_size):
    pad_path = self._pad_path(pad_size)

    bg_brush = QtGui.QBrush(QtCore.Qt.white)
    sel_brush = QtGui.QBrush(QtCore.Qt.lightGray)
    flash_brush = QtGui.QBrush(QtCore.Qt.red)

    border_pen = QtGui.QPen(QtGui.QColor(QtCore.Qt.black))
    groove_pen = QtGui.QPen(QtGui.QColor(QtCore.Qt.lightGray))

    painter.fillPath(pad_path, bg_brush)

    if self._key_state[key_state[0]]:
      painter.fillPath(self._pad_dir_path(LEFT, pad_size), sel_brush)
    if self._key_state[key_state[1]]:
      painter.fillPath(self._pad_dir_path(RIGHT, pad_size), sel_brush)
    if self._key_state[key_state[2]]:
      painter.fillPath(self._pad_dir_path(UP, pad_size), sel_brush)
    if self._key_state[key_state[3]]:
      painter.fillPath(self._pad_dir_path(DOWN, pad_size), sel_brush)

    painter.fillRect(0.6*pad_size,-0.05*pad_size,0.3*pad_size,0.1*pad_size,flash_brush)
    painter.fillRect(-0.9*pad_size,-0.05*pad_size,0.3*pad_size,0.1*pad_size,flash_brush)
    painter.fillRect(-0.05*pad_size,0.6*pad_size,0.1*pad_size,0.3*pad_size,flash_brush)
    painter.fillRect(-0.05*pad_size,-0.9*pad_size,0.1*pad_size,0.3*pad_size,flash_brush)

    painter.setPen(groove_pen)
    painter.drawLine(-0.3*pad_size, -0.3*pad_size, 0.3*pad_size, 0.3*pad_size)
    painter.drawLine(0.3*pad_size, -0.3*pad_size, -0.3*pad_size, 0.3*pad_size)

    painter.setPen(border_pen)
    painter.drawPath(pad_path)

    fm = painter.fontMetrics()
    to = QtGui.QTextOption()
    to.setAlignment(QtCore.Qt.AlignHCenter)
    th = fm.lineSpacing()
    ty = -1.2*pad_size-th
    for line in reversed(label.split()):
      painter.drawText(QtCore.QRectF(-pad_size, ty, 2*pad_size, th), line, to)
      ty -= th

  def _pad_path(self, size, stem_width=0.3):
    path = QtGui.QPainterPath()
    a = size*stem_width
    b = size

    path.moveTo(-a,-b)
    path.lineTo(a,-b)
    path.lineTo(a,-a)
    path.lineTo(b,-a)
    path.lineTo(b,a)
    path.lineTo(a,a)
    path.lineTo(a,b)
    path.lineTo(-a,b)
    path.lineTo(-a,a)
    path.lineTo(-b,a)
    path.lineTo(-b,-a)
    path.lineTo(-a,-a)

    path.closeSubpath()
    return path
  
  def _pad_dir_path(self, direction, size, stem_width=0.3):
    path = QtGui.QPainterPath()
    a = size*stem_width
    b = size

    path.moveTo(0,0)

    if direction == RIGHT:
      path.lineTo(a,a)
      path.lineTo(b,a)
      path.lineTo(b,-a)
      path.lineTo(a,-a)
    elif direction == UP:
      path.lineTo(a,-a)
      path.lineTo(a,-b)
      path.lineTo(-a,-b)
      path.lineTo(-a,-a)
    elif direction == DOWN:
      path.lineTo(a,a)
      path.lineTo(a,b)
      path.lineTo(-a,b)
      path.lineTo(-a,a)
    elif direction == LEFT:
      path.lineTo(-a,a)
      path.lineTo(-b,a)
      path.lineTo(-b,-a)
      path.lineTo(-a,-a)
    else:
      raise RuntimeError('invalid direction: %s' % (str(direction),))

    path.closeSubpath()
    return path

def main():
  app = Application()
  win = ControllerWindow()
  win.show()
  app.exec_()

if __name__ == '__main__':
  main()
