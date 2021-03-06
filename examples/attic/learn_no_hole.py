import os 
from datetime import datetime
import gym
import gym_kuka_mujoco
import numpy as np

from stable_baselines import PPO2
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv, VecNormalize
from stable_baselines.common.policies import MlpPolicy

num_env = 8

day, time = datetime.now().isoformat().split('T')
tensorboard_logdir = os.path.join(
    os.environ['OPENAI_LOGDIR'],
    'stable',
    day,
    time,
    'cirriculum_learning')

actor_options = {
    'learning_rate': 1e-3,
    # 'learning_rate': lambda a: a*1e-3 + (1-a)*1e-4,
    'gamma':1,
    'verbose':0,
    #'n_steps':256,
    'n_steps':2048,
    'ent_coef':1e-2,
}

learning_options = {
    'total_timesteps': int(2e6)
}

# Create the environment
print('\t--setting up environments')
envs = [gym.make('PegInsertionNoHole-v0') for _ in range(num_env)]

# Wrap in a try statement to close the environment properly.
try:
    print('\t--instantiating vectorized environment')
    env = SubprocVecEnv([lambda: e for e in envs])
    # env = DummyVecEnv([lambda: e for e in envs])
    env = VecNormalize(env, training=True, norm_reward=False, clip_obs=np.inf, clip_reward=np.inf)

    # Create the actor and learn
    print('\t--setting up actor')
    actor_options['tensorboard_log'] = os.path.join(tensorboard_logdir,'PegInsertionNoHole-v0')
    print('\t--learning')
    model = PPO2(MlpPolicy, env, **actor_options)
    
    model.learn(**learning_options)
    save_path = os.path.join(actor_options['tensorboard_log'],'model')
    running_average_path = actor_options['tensorboard_log']
    model.save(save_path)
    env.save_running_average(running_average_path)
finally:
    env.close()


# Visualize the solution
env = gym.make('PegInsertionNoHole-v0')
env = DummyVecEnv([lambda: env])
env = VecNormalize(env, training=False, norm_reward=False, clip_obs=np.inf, clip_reward=np.inf)
env.load_running_average(running_average_path)
obs = env.reset()
while True:
    action, _states = model.predict(obs)
    obs, rewards, dones, info = env.step(action)
    env.render()
    if dones[0]:
        env.reset()