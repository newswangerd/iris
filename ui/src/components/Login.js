import React, { useContext, useState } from "react";
import {
  Box,
  VStack,
  FormControl,
  FormLabel,
  Input,
  Button,
} from "@chakra-ui/react";
import { TranslationsContext } from "../context.js";

const Login = ({ client, setView }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const t = useContext(TranslationsContext);

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
            <FormLabel htmlFor="username">{t("Username")}</FormLabel>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </FormControl>
          <FormControl>
            <FormLabel htmlFor="password">{t("Password")}</FormLabel>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </FormControl>
          <Button type="submit">{t("Login")}</Button>
        </VStack>
      </form>
    </Box>
  );
};

export default Login;
