from math import pi, sin, cos

from pyglet.gl import *
import pyglet

from shader import Shader

window = pyglet.window.Window(fullscreen=True)

class ShaderGroup(pyglet.graphics.Group):
  def __init__(self, shader, *args, **kwargs):
    super(ShaderGroup, self).__init__(*args, **kwargs)
    self.shader = shader

  def set_state(self):
    self.shader.bind()

  def unset_state(self):
    self.shader.unbind()

class Floor(object):
  def __init__(self, batch = None, group = None):
    # Create a batch if necessary
    if batch is None:
      batch = pyglet.graphics.Batch()
    self.batch = batch

    self.shader = Shader(
    vert = ['''
    void main() {
      // transform the vertex position
      gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
      // pass through the texture coordinate
      gl_TexCoord[0] = gl_MultiTexCoord0;
    }
    '''],
    frag = ['''
    void main() {
      vec2 f = floor(mod(4.f * gl_TexCoord[0].xy, 2));
      float check = 0.5f + 0.25f * mod(dot(f, vec2(1,1)), 2);
      gl_FragColor = vec4(check,check,check,1);
    }
      '''])
    self.group = ShaderGroup(self.shader, parent=group)
    self.floor = self.batch.add(
        4, pyglet.gl.GL_QUADS, self.group,
        ('v3f', (-20,-1,-20, -20,-1,20, 20,-1,20, 20,-1,-20)),
        ('t2f', (-20,-20, -20,20, 20,20, 20,-20))
    )

  def draw(self):
    self.batch.draw()


class Scene(pyglet.graphics.Group):
  def __init__(self, *args, **kwargs):
    super(Scene, self).__init__(*args, **kwargs)
    self.batch = pyglet.graphics.Batch()

    self.floor = Floor(batch=self.batch, group=self)

    self.ry = 0
    pyglet.clock.schedule(self.update)
  
  def draw(self):
    self.batch.draw()

  def update(self, dt):
    self.ry += dt * 30
    self.ry %= 360

  def set_state(self):
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0, 0, -4)
    glRotatef(self.ry, 0, 1, 0)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glColor3f(1, 0, 0)
    
    glDisable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)

scene = Scene()

@window.event
def on_resize(width, height):
  glViewport(0, 0, width, height)
  glMatrixMode(GL_PROJECTION)
  glLoadIdentity()
  gluPerspective(60., width / float(height), .1, 100.)
  glMatrixMode(GL_MODELVIEW)
  return pyglet.event.EVENT_HANDLED

@window.event
def on_draw():
  window.clear()
  scene.draw()

pyglet.app.run()
