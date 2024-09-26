import React, { useEffect, useState } from "react";
import {
  VStack,
  Box,
  Menu,
  Button,
  MenuItem,
  MenuButton,
  MenuList,
  FormControl,
  FormLabel,
  Input,
  Select,
  Modal,
  ModalBody,
  ModalFooter,
  ModalOverlay,
  ModalContent,
  ModalCloseButton,
  Center,
  useDisclosure,
} from "@chakra-ui/react";
import { ChevronDown } from "lucide-react";
import QRCode from "react-qr-code";

const ControlPanel = ({ client }) => {
  const [userList, setUserList] = useState([]);
  const [name, setName] = useState("");
  const [language, setLanguage] = useState("en");
  const [formUpdated, setFormUpdated] = useState(0);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [authUrl, setAuthUrl] = useState(null);

  useEffect(() => {
    client.user_list().then((resp) => {
      return setUserList(resp.data);
    });
  }, [formUpdated]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const role = "user";
    client
      .user_create({ name, language, role })
      .then(() => setFormUpdated((i) => i + 1));
  };

  const getAuthCode = (user) => {
    client.user_auth_code(user).then((resp) => {
      setAuthUrl(window.location.origin + "?auth_code=" + resp.data.auth_code);
      onOpen();
    });
  };

  const closeQR = (e) => {
    setAuthUrl(null);
    onClose(e);
  };

  return (
    <VStack alignItems={"left"} padding={"20px"}>
      <Box height={"50px"} />

      <Box>
        <h1>Edit User</h1>
      </Box>
      <Box>
        <hr />
      </Box>
      {userList.map((user) => (
        <Box key={user.name}>
          <Menu>
            <MenuButton as={Button} rightIcon={<ChevronDown />}>
              {user.name}
            </MenuButton>
            <MenuList>
              <MenuItem onClick={() => getAuthCode(user)}>QR Code</MenuItem>
              <MenuItem>Logout</MenuItem>
              <MenuItem>Delete</MenuItem>
            </MenuList>
          </Menu>
        </Box>
      ))}
      <Box height={"50px"} />
      <Box>
        <h1>Add User</h1>
      </Box>
      <Box>
        <hr />
      </Box>
      <Box>
        <form onSubmit={handleSubmit}>
          <VStack spacing={4}>
            <FormControl>
              <FormLabel htmlFor="name">Name</FormLabel>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </FormControl>
            <FormControl>
              <FormLabel htmlFor="language">Language</FormLabel>
              <Select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="en">en</option>
                <option value="ru">ru</option>
                <option value="es">es</option>
              </Select>
            </FormControl>
            <Button type="submit">Add User</Button>
          </VStack>
        </form>
      </Box>
      <>
        <Modal isOpen={isOpen} onClose={closeQR}>
          <ModalOverlay />
          <ModalContent>
            <ModalCloseButton />
            <ModalBody>
              <Center padding={"20px"}>
                {authUrl ? <QRCode size={256} value={authUrl} /> : null}
              </Center>
            </ModalBody>
          </ModalContent>
          <ModalFooter />
        </Modal>
      </>
    </VStack>
  );
};

export default ControlPanel;
