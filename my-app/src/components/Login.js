import React, { useState } from "react";
import {
  Box,
  VStack,
  FormControl,
  FormLabel,
  Input,
  FormErrorMessage,
  Button,
} from "@chakra-ui/react";

const Login = ({ client, setView }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    client
      .password_login({ username, password })
      .then(() => setView("interpreter"))
      .catch(() => {
        setUsername("");
        setPassword("");
      });
  };

  return (
    <Box maxW="sm" mx="auto" mt={8}>
      <form onSubmit={handleSubmit}>
        <VStack spacing={4}>
          <FormControl>
            <FormLabel htmlFor="username">Username</FormLabel>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </FormControl>
          <FormControl>
            <FormLabel htmlFor="password">Password</FormLabel>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </FormControl>
          <Button type="submit">Login</Button>
        </VStack>
      </form>
    </Box>
  );
};

export default Login;
