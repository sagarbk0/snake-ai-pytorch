▶ Version 3.0 — Zhepei's Implementation 
	▶ Notes:
		• Corrected code with introduction of frame_timeout_period
		• Modifications: 
			◇ Timeout Function: P_Steps

	▶ Colision Function()
		• Reward (r) = -10

	▶ Timeout Function()
		• Reward (r) = -0.5 / len(self.snake)
		• Num of Steps (P) = 0.7*len(self.snake) + 10
