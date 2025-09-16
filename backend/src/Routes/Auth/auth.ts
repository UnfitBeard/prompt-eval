import express from 'express';
import {
  githubAuthRedirect,
  login,
  registration,
} from '../../Controllers/Auth/auth';

const router = express.Router();

router.post('/login', login);
router.post('/register', registration);
router.post('/githubAuth', githubAuthRedirect);
export default router;
