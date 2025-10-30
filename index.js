import express from "express";
import dotenv from "dotenv";
import authRoutes from "./authRoutes.js";
import { requireAuth } from "./authMiddleware.js";
import { connectAndSync } from "./db.js";

dotenv.config();

async function start() {
  try {
    await connectAndSync(); // connect to DB, sync models

    const app = express();
    app.use(express.json());

    app.use("/auth", authRoutes);

    app.get("/me", requireAuth, (req, res) => {
      res.json({
        userId: req.user.userId,
        email: req.user.email,
        isAdmin: req.user.isAdmin
      });
    });

    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
      console.log(`API running on port ${PORT}`);
    });
  } catch (e) {
    console.error("Failed to start server:", e);
    process.exit(1);
  }
}

start();
