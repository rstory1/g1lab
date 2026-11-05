# Moving the G1's arms from your own program

You write a program that sends joint angles. The robot moves its arms and
hands to those angles, joint by joint. You control both arms (7 joints each) and both hands
(7 joints each). The robot keeps its own balance and legs, so you never have
to think about standing up.

**Right now this runs on the simulated robot.** Your program does not change
when it moves to the real one.

**The easier way: the `g1lab` package** ([guide.md](guide.md)). It keeps
sending for you, reads the sensors, and names each problem. This guide shows
the plain messages underneath it, which still work as they are.

## What you need

- Python 3 and one package: `pip install pyzmq`
- The **address** of the robot computer (in the lab, `192.168.123.222`) and the **port**, normally `5600`.
- A **name** for yourself, such as `ana`. Every message carries it, and the operator sees it on screen.

**In the lab, the lab board** shows whether a session is on, who has the
robot, who is next, and what the robot's camera sees: open
`http://192.168.123.222:8090/` in a browser on the Robot Network (wired, with your
address set by hand: [camera_quickstart.md](camera_quickstart.md), section 1). It also has
the `g1lab` package to download ([guide.md](guide.md)).

## A program from scratch

The whole idea fits in a few lines:

```python
import json, math, time
import zmq

sock = zmq.Context().socket(zmq.REQ)
sock.setsockopt(zmq.RCVTIMEO, 2000)             # give up after 2 s without an answer
sock.connect("tcp://192.168.123.222:5600")

def send(msg):
    sock.send(json.dumps(msg).encode())
    return json.loads(sock.recv())              # always read the answer before sending again

home = send({"client": "YOURNAME", "cmd": "info"})["home"]

t0 = time.time()
while time.time() - t0 < 20:
    arm = list(home["right_arm"])
    arm[0] = math.radians(-60)                  # shoulder_pitch: raise the arm forward
    arm[3] = math.radians(20)                   # elbow
    reply = send({"client": "YOURNAME", "right_arm": arm})
    if not reply["ok"]:
        print(reply["error"])
    time.sleep(1 / 30)                          # about 30 messages a second

send({"client": "YOURNAME", "cmd": "release"})  # done: the arm goes home
```

Three rules come from the way the connection works:

- **Send, then read the answer, then send again.** You must read every answer before the next send, or the socket raises an error.
- **Keep sending.** Send 20 to 50 messages a second, even when the pose isn't changing. If the robot hears nothing for 1 second, it decides your program has stopped and puts the arms down.
- **Angles are in radians.** Use `math.radians(degrees)` if you think in degrees.

## The message

```json
{"client": "YOURNAME",
 "right_arm":  [shoulder_pitch, shoulder_roll, shoulder_yaw, elbow, wrist_roll, wrist_pitch, wrist_yaw],
 "right_hand": [thumb_0, thumb_1, thumb_2, middle_0, middle_1, index_0, index_1]}
```

- Send any of `left_arm`, `right_arm`, `left_hand` and `right_hand`. Each one is a list of exactly 7 numbers.
- A group you leave out stays where it was. At the start, that is the home pose.

The answer looks like:

```json
{"ok": true, "phase": "live", "clamped": {"right_arm": ["elbow"]}}
```

- `clamped` means you asked for more than a joint can do. The robot moved that joint as far as it is allowed, and the list names the joints.
- `held` means the arms stopped part way to your pose, because going further would have hit something. The arm tries to go round by itself; if `held` stays, send a different pose.
- `resting` means an arm was held up too long and is resting by its side. The number is the seconds left; see [Safety](#what-the-robot-does-to-keep-everyone-safe).
- `phase` tells you what the robot is doing:

| phase | what it means for you |
|---|---|
| `waiting` | the session has started; nothing moves yet |
| `settling` | the robot is easing into its starting pose, then towards your angles |
| `live` | the robot is following you |
| `homing` | time is up; the arms are going down and your messages are ignored |
| `ended` | the session is over; your program should stop |

## Which way the joints turn

Stand behind the robot, so its left is your left.

### Arms

| # | joint | what a positive angle does |
|---|---|---|
| 0 | shoulder_pitch | swings the arm **backward**. Use a **negative** angle to raise it forward: −1.57 is roughly straight ahead. |
| 1 | shoulder_roll | **left arm:** lifts it out to the side. **Right arm:** brings it in across the body. To lift the right arm out, use a negative angle. |
| 2 | shoulder_yaw | twists the upper arm. Left: the forearm swings outward. Right: it swings inward. |
| 3 | elbow | **0 is a right angle**, with the forearm pointing forward. About +1.57 straightens the arm. Negative bends it further, bringing the hand up toward the shoulder. |
| 4 | wrist_roll | turns the hand like a doorknob |
| 5 | wrist_pitch | bends the hand up and down |
| 6 | wrist_yaw | bends the hand side to side |

Shoulder roll and shoulder yaw are **mirrored**. A pose that looks the same on
both sides needs opposite signs for those two joints on the right arm. Shoulder
pitch and elbow have the same sign on both sides.

**Home** is the robot's normal standing pose: arms hanging slightly forward,
elbows a little bent, hands open. Its exact numbers are in the `info` answer
as `home`. Start every pose from `home` and change only the joints you care
about. A pose of all zeros is refused: it puts the elbows at right angles and
the two hands almost touching.

### Hands

| # | joint | finger |
|---|---|---|
| 0 | thumb_0 | thumb, swinging across the palm |
| 1 | thumb_1 | thumb, base bend |
| 2 | thumb_2 | thumb, tip bend |
| 3 | middle_0 | middle finger, base |
| 4 | middle_1 | middle finger, tip |
| 5 | index_0 | index finger, base |
| 6 | index_1 | index finger, tip |

- All zeros is an **open** hand.
- On the **right** hand, fingers close with **positive** angles and the thumb tip with a negative one.
- The **left** hand is the mirror image: fingers close with **negative** angles and the thumb tip with a positive one.
- Ask `info` for the exact range of each joint.

**The right middle finger is stuck.** Its base joint is broken on this robot and
is held at 1.56 whatever you send. The right middle finger always looks partly
bent, and that is expected.

## What the robot does to keep everyone safe

You don't need to do anything about these, but they explain what you'll see.

- **Big jumps are smoothed.** If you send a pose far from the current one, the arm moves there over a short time instead of snapping.
- **Out-of-range angles are clamped.** The joint goes as far as allowed, and the answer lists it under `clamped`.
- **Fast arms are slowed.** If your pose would move a hand faster than 1.2 metres a second, the whole arm slows down.
- **Poses that hit the robot are refused.** If a hand would touch the body, the head or the other hand, or an arm would touch a leg, the answer has `"ok": false` and says what would be hit. The arms stay where they were.
- **The path is checked too.** If your pose is fine but the way there is not, the arms stop at the last safe point and the answer has `held`. The arm then swings out to the side to go round, if it can.
- **Raised arms get a rest.** Holding an arm up makes its shoulder motor hot. After 30 seconds raised, the arm goes down and rests for about 15 seconds, then follows you again. Plan programs that lower the arms now and then.
- **Silence puts the arms down.** After 1 second with no messages, the arms go slowly down and the hands open. Send again and the robot comes back to you.
- **One student at a time.** Someone else gets "*ana has the robot*" until you send `release` or stop sending for 10 seconds.
- **The operator and the spotter can always step in.** They can open the hands or end the session at any time.

### How closely the joints follow

Each joint is driven to the angle you send. On the simulated robot:

- **A pose you hold** settles within about 2° of your angles. Most joints get
  within 4°.
- **A pose that is moving** trails by about 4°, and up to 10° in a quick wave.
  The arm follows a fraction of a second behind you.

So if you send a pose and keep sending it, the robot gets there. If your
program needs to know where the arm really is, allow a few degrees.

The robot keeps its own balance with its legs, so moving the arms fast can
make it sway a little. That is normal.

## When something goes wrong

| You see | What to do |
|---|---|
| `no answer from ... -- is a session running?` | Check the address and port (in the lab: `192.168.123.222`, `5600`). The operator must start a session before your program connects. |
| `... has the robot` | Another student is driving. Wait until they finish, or for 10 s after they stop. |
| `... you are 2nd in line` | Keep sending: you get the robot when it is your turn. Stop for 3 s and you lose your place. |
| `no session is running` | The robot is reachable, but the operator has not started a session yet. Keep sending, or wait. |
| `the SIM session is still starting` | The session your program asked for with `r.services.start` is coming up. Keep sending; `control()` waits for it. |
| `the name 'ana' is in use from ...` | Someone on another computer uses that name. Pick another `--name`. |
| `unknown key(s) ['left_arms']` | A typo in a group name. The names are `left_arm`, `right_arm`, `left_hand` and `right_hand`. |
| `right_arm must be a list of 7 numbers` | A list has the wrong length, or contains text or `True`/`False`. |
| `right_arm has NaN or infinity` | Your maths produced "not a number" or infinity, for example from dividing by zero. |
| `Operation cannot be accomplished in current state` | You sent twice without reading the answer in between. Always `recv()` after each `send()`. |
| The robot stopped following and the arms went down | Your program paused for more than 1 second, or the session's time ran out. If `phase` is `ended`, the session is over. |
| `the right hand would hit the head; pose refused` | That pose puts part of the robot into itself. Change that arm's angles, often shoulder_roll or elbow. |
| `held` in the answer | The way to your pose is blocked. The arm tries to go round by itself, swinging out to the side. If `held` stays, go via a pose with the arm further out to the side or forward. |
| `resting` in the answer, and the arm went down | The arm was up for 30 s. Wait for it, and lower the arms between raises. |
| The arm doesn't quite match your angles | See the section above. Fast movement lags; held poses settle within a few degrees. |
