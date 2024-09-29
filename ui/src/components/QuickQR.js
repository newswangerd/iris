import React, { useContext, useEffect, useState } from "react";
import {
  Box,
  Button,
  FormControl,
  Input,
  Select,
  Modal,
  ModalBody,
  ModalFooter,
  ModalOverlay,
  ModalContent,
  ModalCloseButton,
  ModalHeader,
  Center,
  Wrap,
  Divider,
  WrapItem,
  HStack,
  Text,
  Flex,
} from "@chakra-ui/react";
import { ChevronDown, Plus } from "lucide-react";
import QRCode from "react-qr-code";

import { TranslationsContext } from "../context.js";

const QuickQR = ({ client, isOpen, onOpen, onClose }) => {
  const [userList, setUserList] = useState([]);
  const [name, setName] = useState("");
  const [language, setLanguage] = useState("en");
  const [formUpdated, setFormUpdated] = useState(0);
  const [authUrl, setAuthUrl] = useState(null);

  const t = useContext(TranslationsContext);

  useEffect(() => {
    client.user_list().then((resp) => {
      return setUserList(resp.data);
    });
  }, [formUpdated]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const role = "user";
    client.user_create({ name, language, role }).then(() => {
      setFormUpdated((i) => i + 1);
      setName("");
      setLanguage("en");
    });
  };

  const getAuthCode = (user) => {
    client.user_auth_code(user).then((resp) => {
      setAuthUrl(window.location.origin + "?auth_code=" + resp.data.auth_code);
    });
  };

  const closeQR = (e) => {
    setAuthUrl(null);
    onClose(e);
  };

  const qrForm = (
    <>
      <ModalBody>
        <Wrap padding={"10px"}>
          {userList.map((user) => (
            <WrapItem key={user.name}>
              <Button onClick={() => getAuthCode(user)}>{user.name}</Button>
            </WrapItem>
          ))}
        </Wrap>
        <Divider />
        <Box padding={"10px"}>
          <Text>{t("Add User")}</Text>

          <form onSubmit={handleSubmit}>
            <HStack spacing={4}>
              <FormControl>
                <Input
                  placeholder={t("Name")}
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </FormControl>
              <FormControl>
                <Select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                >
                  <option value="en">{t("English")}</option>
                  <option value="ru">{t("Russian")}</option>
                  <option value="es">{t("Spanish")}</option>
                </Select>
              </FormControl>
              <Button type="submit">
                <Plus />
              </Button>
            </HStack>
          </form>
        </Box>
      </ModalBody>

      <ModalFooter>
        <Button colorScheme="red" mr={3} onClick={onClose}>
          {t("Close")}
        </Button>
      </ModalFooter>
    </>
  );

  const qrView = (
    <>
      <ModalBody>
        <Center padding={"20px"}>
          {authUrl ? <QRCode size={256} value={authUrl} /> : null}
        </Center>
        {authUrl}
      </ModalBody>

      <ModalFooter>
        <Button onClick={() => setAuthUrl(null)} colorScheme="red" mr={3}>
          {t("Clear")}
        </Button>
      </ModalFooter>
    </>
  );

  return (
    <>
      <Modal size="xl" isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{t("Create QR Code")}</ModalHeader>
          <ModalCloseButton />
          {authUrl ? qrView : qrForm}
        </ModalContent>
      </Modal>
    </>
  );
};

export default QuickQR;

// <>
//   <Modal isOpen={isOpen} onClose={closeQR}>
//     <ModalOverlay />
//     <ModalContent>
//       <ModalCloseButton />
//       <ModalBody>
//         {authUrl}

//         <Center padding={"20px"}>
//           {authUrl ? <QRCode size={256} value={authUrl} /> : null}
//         </Center>
//       </ModalBody>
//     </ModalContent>
//     <ModalFooter />
//   </Modal>
// </>
