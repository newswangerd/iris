import React, { useContext, useEffect } from "react";
import {
  Button,
  Modal,
  ModalBody,
  ModalFooter,
  ModalOverlay,
  ModalContent,
  ModalCloseButton,
  useDisclosure,
  ModalHeader,
  OrderedList,
  ListItem,
} from "@chakra-ui/react";

import { TranslationsContext } from "../context.js";

import InstructionAnimation from "./InstructionAnimation.js";

const InstructionModal = ({ showOnLoad }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const t = useContext(TranslationsContext);

  useEffect(() => {
    if (showOnLoad) {
      onOpen();
    }
  }, []);

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{t("Instructions")}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <OrderedList>
              <ListItem>{t("Press and hold the red button.")}</ListItem>
              <ListItem>{t("Speak.")}</ListItem>
              <ListItem>{t("Release the button.")}</ListItem>
              <ListItem>
                {t("Your message will be translated and sent to me.")}
              </ListItem>

              <InstructionAnimation />
            </OrderedList>
          </ModalBody>

          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={onClose}>
              {t("Understood")}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default InstructionModal;
