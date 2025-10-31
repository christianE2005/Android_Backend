import express from "express";
import dotenv from "dotenv";
import helmet from "helmet";
import cors from "cors";

import authRoutes from "./routes/authRoutes.js";
import { requireAuth } from "./middleware/authMiddleware.js";
import { connectAndSync } from "./database/db.js";

dotenv.config();

const app = express();

// global middleware
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN || "*" }));
app.use(express.json());

// health and version
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    version: process.env.npm_package_version || "1.0.0",
  });
});

// auth routes
app.use("/auth", authRoutes);

// protected example
app.get("/me", requireAuth, (req, res) => {
  res.json({
    userId: req.user.userId,
    email: req.user.email,
    isAdmin: req.user.isAdmin,
  });
});

async function start() {
  try {
    await connectAndSync(); // connect to DB, sync models

    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
      console.log(
        `API running on port ${PORT} [${process.env.NODE_ENV || "dev"}]`
      );
    });
  } catch (e) {
    console.error("Failed to start server:", e);
    process.exit(1);
  }
}

start();
