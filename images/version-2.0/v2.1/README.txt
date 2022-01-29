▶ Version 2.1 — Zhepei's Implementation 
	▶ Notes:
		• Both of Zhepei's P_Steps & reward is implemented. 
		• Modifications: 
			◇ Timeout Function: P_Steps

	▶ Colision Function()
		• Reward (r) = -10

	▶ Timeout Function()
		• Reward (r) = -0.5 / len(self.snake)
		• Num of Steps (P) = -0.7*len(self.snake) + 10
