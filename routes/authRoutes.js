import express from "express";
import jwt from "jsonwebtoken";
import admin from "firebase-admin";
import { User } from "../models/User.js";

const router = express.Router();

// Initialize Firebase Admin (ADC or serviceAccount file)
// If GOOGLE_APPLICATION_CREDENTIALS is set, applicationDefault works.
if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.applicationDefault()
  });
}

// POST /auth/login
// Body: { firebaseToken: "..." }
router.post("/login", async (req, res) => {
  try {
    const { firebaseToken } = req.body;
    if (!firebaseToken) {
      return res.status(400).json({ error: "firebaseToken is required" });
    }

    // 1. Verify Firebase ID token
    const decoded = await admin.auth().verifyIdToken(firebaseToken);
    const email = decoded.email;
    if (!email) {
      return res.status(400).json({ error: "No email in token" });
    }

    // Optional gmail-only policy
    // if (!email.endsWith("@gmail.com")) {
    //   return res.status(403).json({ error: "Only gmail.com allowed" });
    // }

    // 2. Upsert user using Sequelize
    // findOrCreate is simplest for class use
    const [user] = await User.findOrCreate({
      where: { email },
      defaults: { email, is_admin: false }
    });

    // 3. Create app JWT
    const token = jwt.sign(
      {
        userId: user.id,
        email: user.email,
        isAdmin: user.is_admin
      },
      process.env.JWT_SECRET,
      { expiresIn: "1m" }
    );

    // 4. Return to client
    res.json({
      token,
      user: {
        id: user.id,
        email: user.email,
        isAdmin: user.is_admin
      }
    });
  } catch (err) {
    console.error(err);
    return res.status(401).json({ error: "Invalid Firebase token" });
  }
});

export default router;
