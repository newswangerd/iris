import React from "react";
import { Trash, SendHorizontal } from "lucide-react";
import {
  Button,
  Box,
  Flex,
  Text,
  Card,
  CardBody,
  CardHeader,
  Heading,
} from "@chakra-ui/react";

const Message = ({ message, acceptMsg, rejectMsg, user }) => {
  const msg = {
    paddingLeft: "20px",
    paddingRight: "20px",
  };

  console.log(message);

  return (
    <Card>
      {" "}
      {user.name !== message.user ? (
        <CardHeader>
          <Heading size="md">{message.user} </Heading>
        </CardHeader>
      ) : null}{" "}
      <CardBody>
        <Flex
          justifyContent={"space-between"}
          padding={"10px"}
          alignItems={"center"}
        >
          {message.is_accepted}
          {rejectMsg ? (
            <Button>
              <Trash onClick={rejectMsg} />
            </Button>
          ) : null}

          <Box flex={1} style={msg}>
            <Text fontSize={"lg"}>
              {message.translated_text ? message.translated_text : message.text}
            </Text>
          </Box>
          {acceptMsg ? (
            <Button>
              <SendHorizontal onClick={acceptMsg} />
            </Button>
          ) : null}
        </Flex>
      </CardBody>
    </Card>
  );
};

export default Message;
